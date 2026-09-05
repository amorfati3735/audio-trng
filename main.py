import argparse
import hashlib
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


def load_audio(path: str, sr: int | None = 22050) -> np.ndarray:
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y


def highpass_filter(y: np.ndarray, cutoff: float = 3000, sr: int = 22050) -> np.ndarray:
    sos = butter(10, cutoff, btype="high", fs=sr, output="sos")
    return sosfilt(sos, y)


def extract_mp3_metadata(path: str) -> bytes:
    if mutagen is None:
        return b""
    try:
        audio = MP3(path)
        meta = bytearray()
        meta.extend(audio.info.bitrate.to_bytes(4, "big"))
        meta.extend(audio.info.sample_rate.to_bytes(4, "big"))
        meta.extend(int(audio.info.length * 1000).to_bytes(4, "big"))
        meta.extend(Path(path).stat().st_size.to_bytes(8, "big"))
        meta.extend(audio.info.mode.to_bytes(1, "big"))
        for tag in ("TPE1", "TIT2", "TALB", "TCON", "TDRC"):
            if tag in audio:
                val = str(audio[tag]).encode()
                meta.extend(val)
        return bytes(meta)
    except Exception:
        return Path(path).stat().st_size.to_bytes(8, "big")


def extract_raw_bits(
    y: np.ndarray,
    method: str = "lsb",
    nbits: int = 1,
) -> np.ndarray:
    y_int = (y * 32767).astype(np.int16)

    match method:
        case "lsb":
            shifts = np.arange(nbits, dtype=np.int16)
            bits = ((y_int[:, None] >> shifts) & 1).ravel().astype(np.uint8)
            return bits

        case "diff":
            diff = np.diff(y_int)
            shifts = np.arange(nbits, dtype=np.int16)
            bits = ((diff[:, None] >> shifts) & 1).ravel().astype(np.uint8)
            return bits

        case "zero_cross":
            sign = np.sign(y)
            zc = np.where(np.diff(sign) != 0)[0]
            intervals = np.diff(zc)
            return (intervals % 2).astype(np.uint8)

        case "adc_noise":
            y_int = (y * 32767).astype(np.int16)
            lo = y_int & 3
            hi = (y_int >> 2) & 3
            xor = lo ^ hi
            return xor.ravel().astype(np.uint8)

        case _:
            raise ValueError(f"unknown method: {method}")


def von_neumann_debias(bits: np.ndarray) -> np.ndarray:
    n_even = len(bits) - (len(bits) % 2)
    pairs = bits[:n_even][::2], bits[:n_even][1::2]
    mask = pairs[0] != pairs[1]
    return pairs[0][mask]


def hash_condition(bits: np.ndarray, seed: bytes | None = None, blocks: int = 1) -> bytes:
    raw = np.packbits(bits).tobytes()
    out = bytearray()
    for i in range(blocks):
        h = hashlib.sha256(raw)
        h.update(i.to_bytes(4, "big"))
        if seed:
            h.update(seed)
        out.extend(h.digest())
    return bytes(out)


def bits_to_uint32(bits: np.ndarray) -> list[int]:
    flat = bits[: len(bits) - (len(bits) % 32)]
    packed = np.packbits(flat.reshape(-1, 32)[:, :32])
    return [struct.unpack(">I", packed[i : i + 4])[0] for i in range(0, len(packed), 4)]


def bits_to_image(bits: np.ndarray, size: tuple[int, int] = (512, 512), output: str = "random.png"):
    if Image is None:
        print("error: Pillow not installed. run: uv add Pillow")
        return
    needed = size[0] * size[1] * 8
    if len(bits) < needed:
        bits = np.tile(bits, int(np.ceil(needed / len(bits))))[:needed]
    trimmed = bits[:needed]
    pixels = np.packbits(trimmed).reshape(size[0], size[1])
    img = Image.fromarray(pixels.astype(np.uint8), mode="L")
    img.save(output)
    print(f"saved random grayscale image: {output} ({size[0]}x{size[1]})")


def detect_repetition(data: bytes, window: int = 16) -> list[tuple[int, int, int]]:
    repeats = []
    seen: dict[bytes, int] = {}
    for i in range(len(data) - window + 1):
        chunk = data[i : i + window]
        if chunk in seen:
            repeats.append((seen[chunk], i, seen[chunk] - i))
        else:
            seen[chunk] = i
    return repeats


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
    func = abs(runs - 2 * n * pi * (1 - pi)) / denom
    return func, func < 3.29


def main():
    ap = argparse.ArgumentParser(description="Audio-based True Random Number Generator")
    ap.add_argument("input", nargs="+", help="audio file(s) — merge multiple for more entropy")
    ap.add_argument("-n", "--nbits", type=int, default=1, help="bits per sample (1-16)")
    ap.add_argument(
        "-m", "--method", choices=["lsb", "diff", "zero_cross", "adc_noise"], default="diff"
    )
    ap.add_argument("-c", "--count", type=int, default=256, help="number of 32-bit integers")
    ap.add_argument("--highpass", type=float, default=0, help="highpass cutoff (0 = disable)")
    ap.add_argument("--debias", action="store_true", help="von Neumann debiasing")
    ap.add_argument("--hash", action="store_true", help="SHA-256 conditioning")
    ap.add_argument("--test", action="store_true", help="NIST-style self-tests")
    ap.add_argument("--seed", type=str, help="extra seed string")
    ap.add_argument("--image", type=str, help="save random data as grayscale image (e.g. random.png)")
    ap.add_argument("--image-size", type=int, nargs=2, default=(512, 512), metavar=("W", "H"))
    ap.add_argument("--repcheck", action="store_true", help="check for repeated byte sequences")
    ap.add_argument("--metadata", action="store_true", help="include MP3 metadata as seed")
    args = ap.parse_args()

    for p in args.input:
        if not Path(p).exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    if len(args.input) > 1:
        print(f"merging {len(args.input)} audio files for combined entropy")

    seed_bytes = b""
    if args.seed:
        seed_bytes += args.seed.encode()

    if args.metadata:
        for p in args.input:
            meta = extract_mp3_metadata(p)
            seed_bytes += meta
            if meta:
                print(f"  metadata from {Path(p).name}: bitrate={struct.unpack('>I', meta[:4])[0]}bps")

    y_parts = []
    for p in args.input:
        y = load_audio(p)
        dur = len(y) / 22050
        name = Path(p).name
        print(f"  {name}: {dur:.1f}s, {len(y)} samples")
        if args.highpass:
            y = highpass_filter(y, args.highpass)
        y_parts.append(y)

    y = np.concatenate(y_parts)
    if len(args.input) > 1:
        print(f"  total: {len(y)} samples")

    print(f"extracting: method={args.method}, nbits={args.nbits}")
    bits = extract_raw_bits(y, args.method, args.nbits)
    print(f"  raw bits: {len(bits)}")

    if args.debias:
        bits = von_neumann_debias(bits)
        print(f"  after debias: {len(bits)}")

    blocks = max(1, (args.count * 32 + 255) // 256)
    digest = hash_condition(bits, seed_bytes, blocks=blocks)
    out_bits = np.unpackbits(np.frombuffer(digest, dtype=np.uint8))

    if args.test:
        print("\n--- randomness tests (NIST SP 800-22 style) ---")
        m_stat, m_pass = monobit_test(out_bits)
        print(f"  monobit (freq): stat={m_stat:.4f}  {'PASS' if m_pass else 'FAIL'}")
        r_stat, r_pass = runs_test(out_bits)
        print(f"  runs:           stat={r_stat:.4f}  {'PASS' if r_pass else 'FAIL'}")
        pi = np.mean(out_bits)
        print(f"  P(1) = {pi:.4f}  (ideal: 0.5)")

    if args.image:
        bits_to_image(out_bits, tuple(args.image_size), args.image)

    if args.repcheck:
        data = np.packbits(out_bits).tobytes()
        repeats = detect_repetition(data)
        if repeats:
            print(f"\n--- repetition check: {len(repeats)} repeats found ---")
            for first, second, dist in repeats[:10]:
                print(f"  at offset {first} repeats at {second} (distance={dist})")
            if len(repeats) > 10:
                print(f"  ... and {len(repeats)-10} more")
        else:
            print("\n--- repetition check: no repeated 16-byte windows ---")

    nums = bits_to_uint32(out_bits[: args.count * 32])
    print(f"\n--- {len(nums)} random uint32s ---")
    for n in nums:
        print(n)


if __name__ == "__main__":
    main()
