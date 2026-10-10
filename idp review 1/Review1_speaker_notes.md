# Review 1 — Speaker notes, terminology & presentation prep

Companion to `Review1_presentation.md`. This file is **for you, not for the panel** — it
translates every term in the deck into plain English, gives you the numbers worth memorising,
and rehearses the questions panels actually ask.

---

## 1. The 15-minute plan

| Time | You say | Slide |
|---|---|---|
| 0:00–0:30 | Title + one-line pitch | 1 |
| 0:30–2:15 | Problem → solution → outcome (3 columns) | 2 |
| 2:15–4:00 | The 6 pipeline stages (draw with your finger) | 3 |
| 4:00–5:30 | Six key techniques — read only names + half-line each | 4 |
| 5:30–6:30 | Survey at a glance: 56 refs, 3 themes, counts | 5 |
| 6:30–9:30 | In-depth study: D1 in detail, D2–D6 one breath each | 7 |
| 9:30–11:15 | Six gaps (say the gap, not the ref list) | 8 |
| 11:15–13:00 | Objectives O1–O4 with numbers | 9 |
| 13:00–15:00 | NIST + metrics | 10 |
| 15:00 | Outcome + next review | 11 |

Rules of thumb: comparison tables (slide 6) are **backup** — do not read them aloud. If a
question needs a table, flip to it and point. Move on if you're past time; the panel cares
more about *one clear explanation* than full coverage.

---

## 2. Plain-English glossary

### A. Randomness & cryptography

**Entropy** — how unpredictable something is. A coin flip ≈ 1 bit. A fixed sentence = 0 bits
(it never changes). In audio: how many genuinely surprising bits are hiding in the samples.

**Min-entropy** — the *pessimistic* kind of entropy: how much you can guarantee about the
**worst-case** guess. It's the standard measure for key material, so we quote it in
**bits per byte** (max 8.0; our target ≥ 7.5). Why bytes: a byte is 8 bits, so 7.5 bits of
min-entropy per byte means an attacker's best guess is 2^7.5 ≈ 181× better than blind luck —
still not 256, but good, and honest.

**TRNG (True RNG)** — randomness comes from a *physical* process (noise, jitter, photons).
Unpredictable even if the attacker knows your code.

**PRNG (Pseudorandom RNG)** — an algorithm with a seed. Deterministic: same seed → same
"random" numbers forever. Fine for simulation, **not** for keys on its own.

**CSPRNG / DRBG** — a PRNG that's been hardened for cryptography (NIST SP 800-90A defines
these: Hash-DRBG, CTR-DRBG, HMAC-DRBG). We use `os.urandom` and an AES-CTR DRBG as our
**baselines** — the thing we must look identical to.

**Seed** — the starting value a DRBG needs. Garbage seed in → predictable stream out. That's
exactly what went wrong in Debian (see below).

**Conditioning** — running the raw source through a cryptographic function (SHA-256, AES) to
"clean it up". It works — and it's also why you can no longer tell whether the *source* was any
good. **Our whole pitch: we don't do this.** The hash is a curtain in front of the machinery.

**Hashing vs. extractor** — a hash (SHA-256) *throws away* entropy assumptions and gives you a
fixed-size digest; an **extractor** (Toeplitz matrix, Leftover Hash Lemma) is a mathematically
provably-fair way to squeeze out the usable entropy *while keeping a proof of how much you
kept*. We mention extractors as "the right way to post-process" and note we currently don't
need one — we emit raw bits.

**Bias** — the stream isn't 50/50 (e.g., 52% ones). Bias ≠ non-random, but it *is* usable
signal for an attacker, so it must be measured and, ideally, removed.

**Keystream** — a sequence of random bytes that gets XOR-ed with the plaintext: `cipher = plain
⊕ keystream`. The security of the demo rests entirely on the keystream being unpredictable and
**never reused**.

**Nonce / salt** — extra unique values mixed into keys so the same input doesn't produce the
same output. They must be unpredictable too — hence the need for real randomness.

**Confusion & diffusion** — Shannon's two properties: *confusion* hides the relationship
between key and ciphertext; *diffusion* spreads one plaintext bit's effect over many ciphertext
bits. NPCR/UACI measure diffusion.

**CPA / chosen-plaintext attack** — the attacker picks plaintexts, sees the ciphertexts, and
works backwards to the key. Papers [40], [41], [48] do exactly this to chaos-based ciphers —
that's our argument against algorithmic keystreams.

**Auditability** — our word for "a third party can check where each bit came from". Because we
don't hash, every bit maps to a specific sample in a specific file. Hardware TRNGs can't offer
that.

**The Debian incident [36]** — in 2008 it turned out Debian's OpenSSL package *removed* almost
all randomness from the PRNG seed, so years of generated SSH/SSL keys were predictable from a
tiny space. Great one-line motivation: *"weak entropy has already caused a real mass breach."*

### B. Audio & signal processing

**Sample rate** — how many times per second the waveform is measured (e.g. 44.1 kHz = 44,100
measurements/s). We load at the file's **native** rate — no resampling, so no added artefacts.

**ADC / quantisation noise** — the analogue-to-digital converter rounds each measurement to a
number. That rounding error is physical, uncontrollable, and (partly) random — it's one of our
entropy sources.

**Stereo, L and R** — two channels (Left/Right). Ordinary recordings put the *same* bird in
both channels — the shared part is deterministic-ish, so it can add bias.

**Common-mode rejection (L⊕R)** — XOR (or subtract) the two channels: what's **shared**
disappears, what's **independent noise** stays. Same idea as a differential amplifier.
One-line version: *"we cancel the part both ears agree on."*

**XOR (⊕)** — the workhorse: 0⊕0=0, 1⊕1=0, 0⊕1=1. Random ⊕ random ≈ random; identical ⊕
identical = 0 (that's how cancellation works). It's also what turns three biased views into one
less-biased bit.

**Low bits / LSB (least significant bit)** — the right-most bit of a number: it flips on tiny
noise, so it's the most random and least informative bit. Our **mixed physical extractor** XORs
three different low-bit views of the same sample — different views of the same noise, so bias
cancels while entropy adds up.

**Non-stationary** — statistics that change over time: silence → chirp → silence. Most entropy
maths assume the source is *stationary* (same behaviour throughout). Bird audio isn't. This is
the core of gap G3.

**Frame** — a short slice of audio we analyse as a unit (health-gate decision is made
frame-by-frame). Trimming silence first means the gate never wastes effort on zeros.

**Spectrogram** — a picture of which frequencies are present over time. Papers [20] use it to
measure song "complexity"; we don't need it for extraction, but it's a nice visual on a slide.

**SNR / energy** — loudness relative to noise. Very low-energy frames are mostly silence → few
bits → the health gate drops them.

### C. Standards & tests

**NIST** — the U.S. National Institute of Standards and Technology; its Special Publications
(SP) are the de-facto rulebook for randomness.

- **SP 800-22** — the *test battery* for output bitstreams (15 tests). Answers: "does this
  stream look random?"
- **SP 800-90B** — rules for the *entropy source* itself: health tests + min-entropy
  estimators. Answers: "how much real randomness does the source produce?"
- **SP 800-90A** — how to build a *DRBG* from a seed (our benchmark baseline).
- **SP 800-90C** — how to combine source + conditioning into a full random-bit generator.
- **FIPS 140-3** — U.S. government standard for cryptographic modules; it *requires* a tested
  entropy source (why any of this is mandatory in practice).

**Health test** — a check that runs *while* the source is producing, to catch a broken/stuck
source in real time. Two official ones from 800-90B:
- **RCT (Repetition Count Test)** — "has the same byte repeated too many times in a row?"
  Catches a stuck microphone or pure silence.
- **APT (Adaptive Proportion Test)** — "has one byte value taken over 68% of a recent window?"
  Catches a stuck/dominant value.

**Our health gate** = these ideas applied per frame, with one twist: we **discard** bad frames
instead of reprocessing them. "Discard-only" is the phrase to use — it means no hidden maths is
applied to force a pass.

**Min-entropy estimator** — the tool that turns observed data into a bits/byte number.
- **IID track** — assumes samples are independent and identically distributed (the optimistic
  assumption). We use the histogram/collision estimator on this track.
- **Non-IID track** — corrects for dependence; gives lower (more conservative) numbers.
Paper **D3 (Aslan et al., 2026)** is about how much these two disagree — our justification for
saying out loud *which* track we used.

**p-value** — from a hypothesis test. Null hypothesis = "the stream is random". A tiny p-value
(usually < 0.01) means "this looks *not* random". So p ≥ 0.01 = pass. **α (alpha) = 0.01** is
our chosen risk level (1 in 100 chance of wrongly rejecting a good stream).

**Two-level interpretation** — NIST wants *two* things: (1) each individual sequence must pass,
and (2) across ~100 sequences, the *fraction* passing must lie in the confidence band
(≥ 0.96 for n=100), **and** the p-values themselves must be uniformly distributed. Papers often
report only level 1; we report all three. Saying this out loud earns marks.

**TestU01 / Dieharder / PractRand** — heavier, non-NIST test batteries. Mention as "we can add
these in Review 2"; not required for Review 1.

### D. Image-encryption metrics

**Information entropy (of a cipher image)** — how flat the histogram is. Perfect = 8.0 bits;
we want ≥ 7.99.

**NPCR (Number of Pixels Change Rate)** — change **one** pixel in the plaintext; what
percentage of ciphertext pixels change? Ideal ≈ 99.6094%. Low = the scheme is too
predictable (attacker can see structure).

**UACI (Unified Average Changing Intensity)** — like NPCR but measures *how much* the grey
values changed, on average. Ideal ≈ 33.46%; acceptable band 27–33%.

**Pearson correlation coefficient (r)** — how related two neighbouring pixels are. In a plain
image, horizontal/vertical/diagonal neighbours correlate ≈ 1 (that's why images compress).
In a good cipher, |r| ≈ 0; our target |r| ≤ 0.01.

**Key sensitivity** — flip one bit of the key; the decrypted image should be *completely*
different (≥ 99.6% of pixels differ from the correct-key output). We test a **wrong-audio
control**: decrypt with a different recording → garbage.

**Round-trip identity** — encrypt then decrypt with the right key must reproduce the original
**byte for byte**. Catches bugs where the demo "looks" right but loses data.

**Key space** — total distinct keys. Must be ≥ 2^128 to resist brute force.

### E. Hardware terms you'll hear in Theme 1 (know the one-liners)

| Term | One-liner |
|---|---|
| **Ring oscillator** | A loop of inverters that wobbles in frequency; the wobble (jitter) is random. Needs a chip. |
| **Jitter** | Tiny random timing variations in an oscillator. |
| **Metastability** | A flip-flop stuck between 0 and 1 for a moment — physically random, used as an entropy source. |
| **Memristor** | A resistor that "remembers"; its device-to-device and cycle-to-cycle variation is noisy → random bits. Needs fabrication. |
| **Photonic / quantum RNG** | Measures photon arrival times / vacuum fluctuations. Provably random, expensive, lab-bound. |
| **FPGA / ASIC** | Custom programmable chip / custom manufactured chip. Both = "you need special hardware". |
| **PUF** | Physical Unclonable Function — a chip's unique manufacturing fingerprint; a related but different way to get uniqueness. |

---

## 3. The pipeline in plain English (with follow-ups)

1. **Load & trim** — read the mp3 at its own sample rate; cut leading/trailing silence.
   *If asked:* "we don't resample, so we don't invent or destroy any information."
2. **Stereo common-mode rejection (L⊕R)** — XOR the two channels.
   *If asked:* "anything both channels share — the song, room tone, codec artefacts — cancels;
   only independent noise survives."
3. **Mixed physical extractor** — XOR three low-bit views of each sample.
   *If asked:* "each individual view is biased; XOR-ing independent biased views cancels the
   bias while keeping the entropy. This is the 'method does the work' part."
4. **Health gate (SP 800-90B style)** — test each frame; if it fails (too quiet, too tonal,
   repetitive), **throw the whole frame away**.
   *If asked:* "we never transform bad data into looking-good data; we simply exclude it, and we
   report the discard rate."
5. **Raw bits out** — no SHA-256, no AES, no whitening.
   *If asked:* "that's deliberate: it keeps every bit traceable to a measurement, and it lets us
   measure the *source* rather than the hash."
6. **Outputs** — uint32 stream / grayscale key image / XOR image-encryption demo.

---

## 4. Numbers worth memorising (they will ask)

| Number | Meaning |
|---|---|
| **56 / 51** | total references / journal papers (rubric wants > 50) |
| **71%** | share of papers from 2021–2026 (guideline wants ≥ 70%) |
| **6** | research gaps (rubric wants ≥ 5) |
| **4** | objectives (guideline wants 3–4, measurable) |
| **≥ 7.5 / 8.0** | min-entropy target on raw bytes (O1) |
| **≥ 98%**, p ≥ 0.01, proportion ≥ 0.96, **≥ 10⁶ bits** | NIST SP 800-22 targets (O2) |
| **≥ 20 kbit/s** (pool ≈ 32 kbit/s) | clean entropy throughput (O3) |
| **\|z\| < 3**, autocorr < 0.02 | indistinguishability from `os.urandom` / AES-CTR (O3) |
| **≥ 7.99**, **NPCR ≥ 99.6%**, UACI 27–33%, **\|r\| ≤ 0.01** | encryption metrics (O4) |
| **15** | number of SP 800-22 tests |
| **RCT / APT** | the two SP 800-90B health tests |
| **8.0** | max possible entropy per byte (the ceiling) |
| **33.46% / 99.6094%** | ideal UACI / NPCR |

---

## 5. Likely panel questions + answers

**Q1. Why bird chirps? Why not just white noise or a resistor?**
Three reasons: (1) microphones and recordings are *everywhere* — no extra hardware; (2) field
recordings are strongly non-stationary and wide-band, so they carry ADC noise *plus*
environmental noise *plus* unpredictable vocalisation structure; (3) an open corpus (Xeno-canto)
makes the experiment reproducible by anyone. And nobody has published entropy numbers for this
data — see gap G3.

**Q2. If you don't hash, how do you know the output is random?**
That's the point — we *measure* it instead of assuming it: min-entropy estimation (SP 800-90B)
on the raw stream, plus the full SP 800-22 battery on raw bits, plus a z-test against
`os.urandom`. If the raw stream passes without conditioning, the source is genuinely good.

**Q3. Isn't raw audio heavily biased?**
Yes, raw audio is biased — that's why the extractor (three-view XOR) and the discard-only
health gate exist. We report *before/after* numbers so you can see what each stage contributed.

**Q4. What's the difference between an extractor and a hash?**
A hash gives a fixed digest and is only as good as your assumption that the input was already
unpredictable. An extractor comes with a *proof*: "given min-entropy H, the output is within ε
of uniform." We deliberately use neither, so the source stays visible.

**Q5. How is this different from Avaroğlu et al. (2024)?** (be ready — this is D1)
They threshold *music* and re-optimise the threshold per file with a metaheuristic; one
channel, no source-level entropy figure, validation after processing. We use *field recordings*,
a fixed pipeline, stereo common-mode rejection, a discard-only health gate, and we publish
min-entropy on the **raw** stream.

**Q6. What if the recording is just silence or someone clapping?**
The health gate drops those frames — we report the discard rate. If too much is discarded, the
throughput drops, which is visible in our results rather than hidden.

**Q7. Chaos-based encryption is standard — why reject it?**
Because it keeps being broken: chosen-plaintext attacks recover the key of a whole family of
chaos ciphers [40,41,48] whenever the keystream doesn't depend on the plaintext. We take the
keystream from physics and use it **once per image**.

**Q8. Isn't a min-entropy of 7.5 bits/byte too low for a key?**
It's low for a *single* raw key, and that's honest. Real systems (SP 800-90C) allow a seed
followed by DRBG expansion — we can adopt that in Review 2 without touching the source. Our
claim at Review 1 is about *characterising* the source, not the final key schedule.

**Q9. What is the novelty, in one sentence?**
"An open, conditioning-free, CPU-only path from ordinary bird recordings to validated random
bits — with explicit common-mode rejection and a discard-only health gate — validated on raw
output and benchmarked against standard generators."

**Q10. What's the difference between your Review 1 and Review 2 expectations?**
Review 1 = domain knowledge, literature, gaps, objectives (no code required). Review 2 = 60%
implementation + full system design: project plan, analysis & requirements, system design,
proposed methodology — with running code and at least one measured metric.

**Q11. What is the outcome of this project?**
Working pipeline + demo today; by the final review, a Scopus-indexed journal/conference paper
or a patent, with proof of outcome (acceptance email, submission ID, manuscript, or filed
application number / provisional specification).

**Q12. Isn't audio too slow to be a useful entropy source?**
Measured, not guessed: we report clean bits per second (target ≥ 20 kbit/s, pool ≈ 32 kbit/s
today) — far more than the kbit/s a 128-bit key needs. For most applications you need *keys*,
not gigabytes of randomness.

---

## 6. Delivery tips

**Do**
- Open with the pitch sentence, not with "uh, so, our project is…".
- On the 3-column slide, say **one sentence per column** and move on — the text is for reading.
- Point at the pipeline stages as you name them (slide 3 is the only "diagram" moment).
- For slide 7, spend ~1.5 min on **D1**, then 20–30 s each on D2–D6. Say the *gap* out loud —
  that's the part being marked.
- Say "discard-only health gate", "conditioning-free", "traceable to a measurement" — these are
  your signature phrases; repeat them consistently.
- Give **every team member** at least one section. Panels deliberately ask the person who didn't
  speak to check understanding.
- Keep the tables (slide 6) open in the handout: questions about a specific paper get answered
  by pointing at a row, not by remembering.

**Don't**
- Don't read the 56-row tables aloud.
- Don't say "we hashed the audio" — you didn't, and it contradicts the whole project.
- Don't say "truly random" without a qualifier; say "physically derived, statistically validated".
- Don't claim results you haven't measured. Targets are targets: say "target", not "we achieved",
  until the number exists in `README.md`.
- Don't improvise a citation. If unsure: "that's in reference [x], I'll confirm the exact page."
- Don't argue with the panel — rephrase: "That's fair; the way we handle it is…"

**Opening line (memorise):**
> "We generate true random numbers from the physical noise in bird recordings — no algorithm,
> no hash, no special hardware. Every output bit can be traced back to a sample in a file."

**Closing line:**
> "So: 56 papers, 6 gaps, 4 measurable objectives, and a pipeline that already runs. The gaps
> all point at one place — unconditioned entropy from natural audio, validated honestly. That's
> what we're building."

---

## 7. Common mix-ups to avoid

| Wrong | Right |
|---|---|
| "Entropy = randomness of the output" | Entropy is a property of the **source**; tests only try to **disprove** randomness of the output. |
| "NIST 800-22 measures entropy" | 800-22 tests **statistics of the stream**; **90B** estimates **entropy**. |
| "p-value is the probability we're random" | p-value = probability of seeing this data **if** it were random. High p ≠ proof of randomness. |
| "NPCR and UACI test security" | They measure **differential sensitivity** (diffusion). Security needs them *plus* attack analysis. |
| "Chaotic = random" | Chaos is **deterministic** — reproducible from the equation and seed. That's why it's a pseudorandom source. |
| "Stereo XOR = averaging" | XOR **cancels shared content**; averaging would blend it in. |
| "We use SHA-256 for safety" | We explicitly **don't** — that's the project's differentiator. |
| "56 papers, all journal" | 56 total = **51 journal** + 2 conference + 3 NIST standards. Be precise; they will check. |

---

## 8. Before you present — checklist

- [ ] Placeholders filled: `[PROJECT ID]`, names, register numbers, guide details.
- [ ] Every **†** page range confirmed against the publisher record.
- [ ] Author lists completed where the reference still says "et al." (APA 7 wants up to 20).
- [ ] Figures render at slide size (`diagrams/fig*.png`); `fig5` for results, `fig6` for gaps.
- [ ] Repo link opens (`github.com/amorfati3735/audio-trng`); demo image encrypt/decrypt runs.
- [ ] Each team member knows which slide they own **and** can explain slides they don't own.
- [ ] Rehearsed twice with a timer; second run under 15:00.

---

*Companion to `Review1_presentation.md`. Original long-form document:
`Review1_audio_trng.md`.*
