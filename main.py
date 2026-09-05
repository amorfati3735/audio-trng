#!/usr/bin/env python3
"""Audio-based True Random Number Generator + image encryption demo.

Randomness comes ONLY from physical processes in the audio signal
(ADC quantization noise, environmental noise, non-stationary signal
content). No cryptographic conditioning (SHA-256 etc.) is used — the
extracted bits stand on their own.

Subcommands:
  gen      chirp*.mp3              -> random uint32s / grayscale image / raw bytes
  encrypt  chirp*.mp3 -i img.png   -> cipher.png   (keystream XOR)
  decrypt  chirp*.mp3 -i ciph.png  -> plain.png    (same keystream XOR)
"""
import argparse
import struct
import sys
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import butter, sosfilt

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import mutagen
    from mutagen.mp3 import MP3
except ImportError:
    mutagen = None

SR = 22050
METHODS = ("lsb", "diff", "zero_cross", "adc_noise", "mixed")


# ---------------------------------------------------------------------------
# Audio loading / filtering
# ---------------------------------------------------------------------------
def load_audio(path: str, sr: int = 0):
    """Load a file, returning (samples, sr). Samples are 1-D for mono
    sources or (channels, n) for stereo. sr=0 keeps the file's native
    sample rate — more samples/sec = more physical entropy per minute."""
    if sr == 0:
        sr = None
    y, sr_out = librosa.load(path, sr=sr, mono=False)
    return y, sr_out


def highpass_filter(y: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    sos = butter(10, cutoff, btype="high", fs=sr, output="sos")
    return sosfilt(sos, y)


def silence_bounds(y: np.ndarray, sr: int = SR, thresh: float = 1e-4,
                   win: int = 2048, hop: int = 1024) -> tuple[int, int]:
    """Onset/offset sample indices where the RMS envelope exceeds thresh."""
    frames = librosa.util.frame(y, frame_length=win, hop_length=hop)
    rms = np.sqrt(np.mean(frames**2, axis=0))
    on = np.nonzero(rms > thresh)[0]
    if len(on) == 0:
        return 0, len(y)
    start = int(on[0]) * hop
    end = min(int(on[-1] + 1) * hop + win, len(y))
    return start, end


def trim_silence(y: np.ndarray, sr: int = SR, thresh: float = 1e-4,
                 win: int = 2048, hop: int = 1024) -> np.ndarray:
    """Cut leading/trailing silence (incl. MP3 decoder lead-in zeros).

    Zero/LSB-constant regions carry no entropy and bias the start of the
    stream. Non-silent bounds are computed once and applied identically to
    every channel, so multi-channel arrays keep matching lengths.
    """
    if y.ndim == 1:
        y = y[None, :]
    start, end = silence_bounds(y.mean(axis=0), sr, thresh, win, hop)
    trimmed = y[:, start:end]
    return trimmed[0] if trimmed.shape[0] == 1 else trimmed


def common_mode_xor(y: np.ndarray) -> np.ndarray:
    """Stereo common-mode rejection (L XOR R) before entropy extraction.

    Both channels of a stereo recording carry the same signal, tone, and
    decoder-quantization LSB patterns (common-mode). XOR-ing the digitized
    samples cancels that correlated component and leaves the uncorrelated
    left/right noise — which is the actual entropy. Returns a single stream
    (mono). No-op for mono input.
    """
    if y.ndim == 1 or y.shape[0] == 1:
        return y
    l = (y[0] * 32767).astype(np.int16)
    r = (y[1] * 32767).astype(np.int16)
    return ((l ^ r).astype(np.float64) / 32767.0)[None, :]


def file_fingerprint(path: str) -> dict:
    """Non-random info about a source file (shown only, never mixed into bits)."""
    info = {"file": str(Path(path).name), "bytes": Path(path).stat().st_size}
    if mutagen is not None:
        try:
            a = MP3(path)
            info.update(
                bitrate=a.info.bitrate,
                sample_rate=a.info.sample_rate,
                length=round(a.info.length, 1),
                mode=a.info.mode,
            )
        except Exception:
            pass
    return info


# ---------------------------------------------------------------------------
# Entropy extraction  (the core — pure physical bits, no hashing anywhere)
# ---------------------------------------------------------------------------
def extract_raw_bits(y: np.ndarray, method: str = "mixed", nbits: int = 1) -> np.ndarray:
    y_int = (y * 32767).astype(np.int16)
    shifts = np.arange(nbits, dtype=np.int16)

    if method == "lsb":
        return ((y_int[:, None] >> shifts) & 1).ravel().astype(np.uint8)

    if method == "diff":
        d = np.diff(y_int)
        return ((d[:, None] >> shifts) & 1).ravel().astype(np.uint8)

    if method == "zero_cross":
        sign = np.sign(y)
        zc = np.where(np.diff(sign) != 0)[0]
        intervals = np.diff(zc)
        return (intervals % 2).astype(np.uint8)

    if method == "adc_noise":
        mask = (1 << nbits) - 1
        x = (y_int & mask) ^ ((y_int >> 2) & mask)
        return ((x[:, None] >> shifts) & 1).ravel().astype(np.uint8)

    if method == "mixed":
        # XOR of three complementary views: raw LSBs, sample-difference LSBs,
        # and shifted-plane LSBs. Independent-ish physical mechanisms cancel
        # any residual bias/correlation present in a single view.
        mask = (1 << nbits) - 1
        a = y_int & mask
        d = np.diff(y_int)
        d = np.concatenate([d, np.zeros(1, dtype=d.dtype)])
        b = d & mask
        c = (y_int >> 2) & mask
        x = a ^ b ^ c
        return ((x[:, None] >> shifts) & 1).ravel().astype(np.uint8)

    raise ValueError(f"unknown method: {method}")


def von_neumann_debias(bits: np.ndarray) -> np.ndarray:
    """Classic debiaser: keep 01->0 / 10->1, discard 00/11. Not a hash."""
    n_even = len(bits) - (len(bits) % 2)
    pairs = bits[:n_even][::2], bits[:n_even][1::2]
    mask = pairs[0] != pairs[1]
    return pairs[0][mask]


def health_gate(bits: np.ndarray, block_bits: int = 16384, zlim: float = 1.0) -> np.ndarray:
    """Discard low-entropy source frames (NIST SP 800-90B-style health check).

    NOT a transform — never alters or expands data, only rejects whole blocks
    whose measured byte-uniformity is statistically suspicious (|z| > zlim).
    Keeps only physical segments that entropy testing judges adequate, so the
    keystream is uniform end-to-end even when the audio has long tonal
    stretches (piano/music) with periodic low-bit structure.
    """
    if block_bits <= 0 or len(bits) < block_bits:
        return bits
    nblocks = len(bits) // block_bits
    blocks = bits[: nblocks * block_bits].reshape(nblocks, block_bits)
    zs = np.array([
        byte_chi2_test(np.packbits(blk).tobytes())[0] for blk in blocks
    ])
    keep = np.abs(zs) <= zlim
    print(f"  health gate: kept {int(keep.sum()):,}/{nblocks:,} blocks "
          f"({100 * keep.mean():.1f}%), dropped {100 * (1 - keep.mean()):.1f}% "
          f"low-entropy audio")
    return blocks[keep].ravel()


# ---------------------------------------------------------------------------
# Randomness tests (NIST SP 800-22 style, all on RAW extracted bits)
# ---------------------------------------------------------------------------
def monobit_test(bits: np.ndarray) -> tuple[float, bool]:
    n = len(bits)
    s = np.sum(2 * bits.astype(np.int8) - 1)
    stat = abs(s) / np.sqrt(n)
    return stat, stat < 3.29


def runs_test(bits: np.ndarray) -> tuple[float, bool]:
    n = len(bits)
    pi = np.mean(bits)
    if abs(pi - 0.5) > 2.0 / np.sqrt(n):
        return float("inf"), False
    runs = 1 + np.sum(bits[1:] != bits[:-1])
    denom = 2 * np.sqrt(n) * pi * (1 - pi)
    stat = abs(runs - 2 * n * pi * (1 - pi)) / denom
    return stat, stat < 3.29


def autocorr_test(bits: np.ndarray) -> tuple[float, bool]:
    n = len(bits) - 1
    x = bits[:-1].astype(np.float32) - bits[:-1].mean()
    y = bits[1:].astype(np.float32) - bits[1:].mean()
    r = float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y) + 1e-12))
    return r, abs(r) < 0.02


def byte_chi2_test(data: bytes) -> tuple[float, bool, float]:
    """Uniformity of the packed byte stream. z ~ N(0,~1); |z|<3 => passes."""
    freqs = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    n = len(data)
    exp = n / 256.0
    chi2 = float(np.sum((freqs - exp) ** 2 / exp))
    z = np.sqrt(2 * chi2) - np.sqrt(2 * 255 - 1)
    pmin = float(-np.log2(freqs.max() / n))  # min-entropy (bits / byte)
    return z, abs(z) < 3.0, pmin


def gen_from_audio(
    files: list[str],
    method: str,
    nbits: int,
    highpass: float,
    debias: bool,
    nbytes: int | None,
    sr: int = 0,
    gate: bool = True,
    gate_block: int = 16384,
    gate_z: float = 1.0,
    xor_channels: bool = True,
):
    """Load & merge all files -> raw bits -> packed bytes.

    Every channel of every file is an independent physical noise stream, so
    stereo sources contribute 2x the entropy. Returns (dur_s, sr_eff,
    bits, data_bytes, per_file_info). nbytes=None returns everything;
    otherwise returns at most nbytes (error if too little).
    """
    y_parts, infos, dur, sr_eff = [], [], 0.0, SR
    for p in files:
        if not Path(p).exists():
            sys.exit(f"error: file not found: {p}")
        y, sr_eff = load_audio(p, sr)
        y = trim_silence(y, sr_eff)          # one trim window for all channels
        if y.ndim == 1:
            y = y[None, :]
        applied_xor = False
        if y.shape[0] > 1 and xor_channels:
            y = common_mode_xor(y)           # L^R: cancel common signal/decoder bias
            applied_xor = True
        dur += y.shape[1] / sr_eff
        if highpass:
            y = np.stack([highpass_filter(y[c], highpass, sr_eff) for c in range(y.shape[0])])
        y_parts.append(y)
        infos.append(file_fingerprint(p))
        label = "L^R (common-mode rejection)" if applied_xor else f"{y.shape[0]} ch"
        print(f"  {Path(p).name}: {y.shape[1]/sr_eff:.1f}s {label} "
              f"({y.shape[1]:,} samples @ {sr_eff} Hz)")

    bits = np.concatenate([
        np.concatenate([extract_raw_bits(ych[c], method, nbits) for c in range(ych.shape[0])])
        for ych in y_parts
    ])
    if debias:
        bits = von_neumann_debias(bits)
    if gate:
        bits = health_gate(bits, gate_block, gate_z)
    data = np.packbits(bits).tobytes()
    if nbytes is not None and len(data) < nbytes:
        bps = len(data) / dur if dur else 0.0
        more_s = (nbytes - len(data)) / bps if bps else float("inf")
        sys.exit(
            f"error: need {nbytes:,} bytes of keystream but the audio pool "
            f"produced {len(data):,} bytes ({len(data)/dur:.0f} bytes/s of "
            f"audio, {dur:.0f}s total).\n"
            f"  Need ~{more_s/60:.0f} more minutes of audio at current settings.\n"
            f"  Hints: pass more/longer files; natural ambience/bird recordings "
            f"yield more clean entropy than music; use a smaller image (an "
            f"academic 512x512 demo needs only ~40s of audio)."
        )
    if nbytes is not None:
        data = data[:nbytes]
    return dur, sr_eff, bits, data, infos


def bits_to_uint32(bits: np.ndarray) -> list[int]:
    flat = bits[: len(bits) - (len(bits) % 32)]
    packed = np.packbits(flat.reshape(-1, 32)[:, :32])
    return [struct.unpack(">I", packed[i : i + 4])[0] for i in range(0, len(packed), 4)]


def detect_repetition(data: bytes, window: int = 16) -> list[tuple[int, int, int]]:
    repeats, seen = [], {}
    for i in range(len(data) - window + 1):
        chunk = data[i : i + window]
        if chunk in seen:
            repeats.append((seen[chunk], i, i - seen[chunk]))
        else:
            seen[chunk] = i
    return repeats
# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------
def _require_pil():
    if Image is None:
        sys.exit("error: Pillow not installed. run: uv add Pillow")


def save_keystream_png(data: bytes, size: tuple[int, int], out: str):
    _require_pil()
    needed = size[0] * size[1]
    if len(data) < needed:
        sys.exit(f"error: need {needed} bytes for a {size[0]}x{size[1]} image, only {len(data)} available")
    arr = np.frombuffer(data[:needed], dtype=np.uint8).reshape(size)
    Image.fromarray(arr, mode="L").save(out)
    print(f"  saved random grayscale key image: {out} ({size[0]}x{size[1]})")


def load_plane(path: str) -> tuple[np.ndarray, str]:
    _require_pil()
    img = Image.open(path)
    if img.mode not in ("L", "RGB", "RGBA"):
        img = img.convert("RGB")
    return np.array(img), img.mode


def xor_with_key(plane: np.ndarray, key: bytes) -> np.ndarray:
    flat = plane.ravel().astype(np.uint8)
    k = np.frombuffer(key, dtype=np.uint8)
    if len(k) < len(flat):
        sys.exit(f"error: key too short ({len(k)} bytes) for image ({len(flat)} bytes)")
    return np.bitwise_xor(flat, k[: len(flat)]).reshape(plane.shape)


def encryption_metrics(plain: np.ndarray, cipher: np.ndarray) -> dict:
    p = plain.ravel().astype(np.float64)
    c = cipher.ravel().astype(np.float64)
    corr = float(np.corrcoef(p, c)[0, 1])
    freqs = np.bincount(cipher.ravel(), minlength=256)
    n = c.size
    exp = n / 256.0
    chi2 = float(np.sum((freqs - exp) ** 2 / exp))
    z = np.sqrt(2 * chi2) - np.sqrt(2 * 255 - 1)
    pmin = float(-np.log2(freqs.max() / n))
    return {"corr": corr, "chi2_z": z, "min_entropy": pmin}


# ---------------------------------------------------------------------------
# Shared extraction CLI args
# ---------------------------------------------------------------------------
def add_extract_args(p):
    p.add_argument("-m", "--method", choices=METHODS, default="mixed",
                   help="lsb/diff/zero_cross/adc_noise, or 'mixed' (default): XOR of three physical views")
    p.add_argument("-n", "--nbits", type=int, default=1, help="bits per sample (1-4)")
    p.add_argument("--highpass", type=float, default=0.0,
                   help="highpass cutoff Hz per file (0 = off; usually not needed)")
    p.add_argument("--debias", action="store_true", help="von Neumann debiasing (halves data)")
    p.add_argument("--sr", type=int, default=0,
                   help="sample rate Hz (0 = native file rate, default; native+stereo yields ~4x entropy of 22 kHz mono)")
    p.add_argument("--no-xor", action="store_true",
                   help="disable stereo L^R common-mode rejection (keeps both channels, ~2x data but biased on tonal sources)")
    p.add_argument("--no-gate", action="store_true",
                   help="disable the entropy health gate (not recommended for music/long sources)")
    p.add_argument("--gate-block", type=int, default=16384,
                   help="health-gate block size in bits (default 16384 = 2048 bytes)")
    p.add_argument("--gate-z", type=float, default=1.0,
                   help="health-gate byte-uniformity z threshold (default 1.0; stricter = cleaner output, more data dropped)")
# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------
def cmd_gen(args):
    dur, sr_eff, bits, data, infos = gen_from_audio(
        args.input, args.method, args.nbits, args.highpass, args.debias, None,
        args.sr, not args.no_gate, args.gate_block, args.gate_z, not args.no_xor
    )
    print(f"  merged: {dur:.1f}s audio @ {sr_eff:,} Hz -> {len(bits):,} raw bits = {len(data):,} bytes "
          f"({len(bits)/dur:.0f} bits/s)")

    if args.metadata:
        for info in infos:
            print(f"  {info['file']}: bitrate={info.get('bitrate', '?')}bps, "
                  f"sr={info.get('sample_rate', '?')}Hz, size={info['bytes']}B")

    if args.test:
        print("\n--- randomness tests (on RAW extracted bits, NO conditioning) ---")
        m, mp = monobit_test(bits)
        r, rp = runs_test(bits)
        ac, acp = autocorr_test(bits)
        z, zp, pmin = byte_chi2_test(data)
        print(f"  monobit (freq):    stat={m:8.4f}  {'PASS' if mp else 'FAIL'}")
        print(f"  runs:              stat={r:8.4f}  {'PASS' if rp else 'FAIL'}")
        print(f"  autocorr (lag 1):  r   ={ac:+8.4f}  {'PASS' if acp else 'FAIL'}")
        print(f"  byte uniformity:   z   ={z:+8.2f}  {'PASS' if zp else 'FAIL'}")
        print(f"  P(1) = {bits.mean():.4f}   (ideal 0.5)")
        print(f"  min-entropy = {pmin:.4f} bits/byte   (8.0 = fully random)")

    if args.image:
        save_keystream_png(data, tuple(args.image_size), args.image)

    if args.repcheck:
        reps = detect_repetition(data)
        if reps:
            print(f"\n--- repetition check: {len(reps)} repeated 16-byte windows (first: offset {reps[0][0]}) ---")
        else:
            print("\n--- repetition check: no repeated 16-byte windows ---")

    if args.out:
        Path(args.out).write_bytes(data)
        print(f"  wrote {len(data)} random bytes -> {args.out}")

    nums = bits_to_uint32(bits[: args.count * 32])
    print(f"\n--- {len(bits) // 32} uint32s total, showing {len(nums)} ---")
    for n in nums:
        print(n)


def cmd_encrypt(args):
    plain, mode = load_plane(args.plain)
    nbytes = plain.size * plain.itemsize
    dur, sr_eff, bits, key, infos = gen_from_audio(
        args.input, args.method, args.nbits, args.highpass, args.debias, nbytes,
        args.sr, not args.no_gate, args.gate_block, args.gate_z, not args.no_xor
    )
    print(f"  keystream: {len(key):,} bytes from {dur:.0f}s audio @ {sr_eff:,} Hz")
    if args.metadata:
        for info in infos:
            print(f"  {info['file']}: bitrate={info.get('bitrate', '?')}bps, "
                  f"sr={info.get('sample_rate', '?')}Hz, size={info['bytes']}B")

    cipher = xor_with_key(plain, key)
    Image.fromarray(cipher, mode=mode).save(args.output)
    if args.key_image:
        save_keystream_png(key, (512, 512), args.key_image)

    met = encryption_metrics(plain, cipher)
    print(f"\n  encrypted {Path(args.plain).name} ({mode}) -> {args.output}")
    print(f"  plain<->cipher correlation: {met['corr']:+.4f}   (0 = no relation, ideal)")
    print(f"  cipher byte uniformity z:   {met['chi2_z']:+.2f}  (PASS if |z| < 3)")
    print(f"  cipher min-entropy:         {met['min_entropy']:.4f} bits/byte   (8.0 ideal)")


def cmd_decrypt(args):
    cipher, mode = load_plane(args.input_file)
    nbytes = cipher.size * cipher.itemsize
    dur, sr_eff, bits, key, _ = gen_from_audio(
        args.random, args.method, args.nbits, args.highpass, args.debias, nbytes,
        args.sr, not args.no_gate, args.gate_block, args.gate_z, not args.no_xor
    )
    plain = xor_with_key(cipher, key)
    Image.fromarray(plain, mode=mode).save(args.output)
    print(f"  decrypted {Path(args.input_file).name} ({mode}) -> {args.output}")
    if args.verify:
        ref, _ = load_plane(args.verify)
        same = bool(np.array_equal(ref, plain))
        print(f"  round-trip vs {Path(args.verify).name}: {'IDENTICAL' if same else 'MISMATCH'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="extract random numbers from audio files")
    g.add_argument("input", nargs="+", help="audio files (pass 5-10 for a bigger entropy pool)")
    add_extract_args(g)
    g.add_argument("-c", "--count", type=int, default=64, help="uint32s to print")
    g.add_argument("--image", type=str, help="save keystream as grayscale PNG")
    g.add_argument("--image-size", type=int, nargs=2, default=(512, 512), metavar=("W", "H"))
    g.add_argument("--out", type=str, help="also write full random bytes to this file")
    g.add_argument("--test", action="store_true", help="run randomness tests on raw bits")
    g.add_argument("--repcheck", action="store_true", help="check for repeated 16-byte windows")
    g.add_argument("--metadata", action="store_true", help="print mp3 fingerprint info")
    g.set_defaults(fn=cmd_gen)

    e = sub.add_parser("encrypt", help="encrypt an image by XOR with audio-derived keystream")
    e.add_argument("input", nargs="+", help="audio key sources (use the same ones to decrypt)")
    add_extract_args(e)
    e.add_argument("-i", "--plain", required=True, help="input (plaintext) image")
    e.add_argument("-o", "--output", required=True, help="output cipher image")
    e.add_argument("--key-image", type=str, help="optional: save 512x512 keystream visualization")
    e.add_argument("--metadata", action="store_true")
    e.set_defaults(fn=cmd_encrypt)

    d = sub.add_parser("decrypt", help="decrypt a cipher image (same audio = same keystream)")
    d.add_argument("random", nargs="+", help="same audio files used for encryption")
    add_extract_args(d)
    d.add_argument("-i", "--input_file", required=True, help="cipher image")
    d.add_argument("-o", "--output", required=True, help="recovered image")
    d.add_argument("--verify", type=str, help="optional plaintext image to verify exact recovery")
    d.set_defaults(fn=cmd_decrypt)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()