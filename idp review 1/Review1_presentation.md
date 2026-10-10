# BACSE291 – Innovative Design Project · Review 1
## Slide source for the 15-minute panel presentation

**Project ID:** [PROJECT ID]
**Project Title:** Generation of True Random Numbers from Bird Chirping
**Academic Year:** 2026–2027 · Review 1 (Panel) · 7 & 14 October 2026

| S.No | Name | Register Number | School |
|------|------|-----------------|--------|
| 1 | [Name 1] | [Reg No 1] | SCOPE |
| 2 | [Name 2] | [Reg No 2] | SCOPE |
| 3 | [Name 3] | [Reg No 3] | SCOPE |
| 4 | [Name 4] | [Reg No 4] | SCOPE |

**Guide:** [Guide Name] · [Designation] · SCOPE

---

> **What this file is.** A talk-ready rewrite of `Review1_audio_trng.md`. One numbered
> section = one slide (or one backup slide). Sentences are short on purpose — read them,
> don't recite them. Numbers, tables and citations are still exact, because the panel
> marks those. Full reference list is at the end (handout, not a slide).
> Companion file: **`Review1_speaker_notes.md`** — plain-English meanings of every term,
> timing plan, and likely panel questions with answers.

---

## Run of show (15:00 total)

| Slide | Section | Time |
|---|---|---|
| 1 | Title + one-line pitch | 0:30 |
| 2 | Problem · Solution · Outcome (3 columns) | 1:45 |
| 3 | How the pipeline works (6 stages) | 1:45 |
| 4 | Six key techniques | 1:30 |
| 5 | Literature survey at a glance (56 refs, 3 themes) | 1:00 |
| 6 | Comparison tables (backup/handout) | (skip; keep for questions) |
| 7 | In-depth study — 6 papers, 2024–2026 | 3:00 |
| 8 | Six research gaps | 1:45 |
| 9 | Objectives O1–O4 | 1:45 |
| 10 | NIST standards, test cases & metrics | 2:00 |
| 11 | Expected outcome + what's next | 0:45 |
| — | References (handout) | — |

Figures available: `diagrams/fig1_system_architecture.png`, `fig2_signal_pipeline.png`,
`fig3_entropy_extraction.png`, `fig4_health_gate.png`, `fig5_validation_results.png`,
`fig6_research_map.png`.

---

## Slide 1 · Title

**Generation of True Random Numbers from Bird Chirping**

*One-line pitch:* "We take ordinary bird recordings and turn the physical noise inside them
into random numbers good enough for cryptography — with no hashing and no special hardware."

---

## Slide 2 · Brief description of the project

**Domain:** Applied Cryptography — physical (non-algorithmic) randomness.
**Application area:** Keys and nonces for devices that have a microphone but no dedicated
random-number chip (IoT nodes, edge sensors, student laptops).

| **1 · Problem** | **2 · Proposed solution** | **3 · Expected outcome** |
|---|---|---|
| Cryptographic systems need unpredictable keys, nonces and salt. Ideally these come from **physical** randomness, not from an algorithm. Today's true random number generators need (a) **custom silicon** — ring-oscillator jitter, memristors, quantum optics — or (b) a **hash function (SHA-256) that re-whitens the output** and makes the actual physical source impossible to audit. When an entropy source goes wrong, real systems break: the 2008 Debian OpenSSL release shipped predictable keys [36]. So the real question is not *"can we make random numbers?"* — it is *"can we get good randomness from a source that is cheap, everywhere, and auditable?"* | We build a TRNG whose randomness comes **only** from the physical noise inside naturally occurring **bird-chirp field recordings**. The **method** does the work, not a hash: (i) **stereo common-mode rejection (L⊕R)** cancels tonal content and decoder artefacts shared by both channels; (ii) a **mixed physical extractor** XORs three complementary low-bit views of every sample; (iii) an **SP 800-90B-style health gate** *discards* statistically poor frames and never rewrites them. Bits go out **unconditioned** and are validated directly, then used as a keystream for an image-encryption demo. **What it delivers:** an open, CPU-only pipeline + raw-bit entropy/statistical report + throughput benchmark vs `os.urandom`/AES-CTR + a working image-encryption demo with standard security metrics. | **Now (already working):** a CPU-only pipeline in the open repo `github.com/amorfati3735/audio-trng` that converts bird recordings into validated random bits and encrypts/decrypts an image — no hashing anywhere. **Eventual outcome (Outcome Analysis, BACSE291):** *Publication in a Scopus-indexed journal* (Published/Accepted 10 · Under review 8 · Communicated 4), and/or *Publication in a Scopus-indexed conference* (Paper presented 10 · Communicated 5), and/or *Patent* (Patent published 10 · Patentability Search Result – Approved 7 · Patent IDF submitted 3). |

**One line to say out loud:** *"Right now we have a working pipeline and a demo; the outcome we
are aiming at by the final review is a Scopus-indexed paper or a filed patent, with proof of
outcome — acceptance email or submission ID for the paper, application number for the patent."*

**Why the approach is different (say this too):** we deliberately *reject* cryptographic
conditioning and instead engineer the extraction method, so **every output bit can be traced
back to a physical measurement**.

---

## Slide 3 · How it works — 6 stages

```
bird recording (mp3/wav, native sample rate)
   → 1. load + trim silence
   → 2. stereo common-mode rejection: L ⊕ R      (kills shared tonal/decoder noise)
   → 3. mixed physical extractor: XOR of 3 low-bit views of each sample
   → 4. SP 800-90B-style health gate: DISCARD bad frames, never transform them
   → 5. raw bitstream  (no SHA-256, no AES, no whitening)
   → 6. outputs: uint32 stream / grayscale key image / XOR image-encryption demo
```

- Stage 2 removes what is **shared** between channels (the deterministic part).
- Stage 3 removes **bias** within a sample (the predictable low bits).
- Stage 4 removes **whole frames** that are too quiet or too tonal — throw-away, not repair.
- Nothing in the chain is a cryptographic hash. Validation is run on the **raw** bits.

*Figure: `diagrams/fig2_signal_pipeline.png`, `fig3_entropy_extraction.png`, `fig4_health_gate.png`.*

---

## Slide 4 · Key techniques in the domain

| # | Technique | What it is (one line) |
|---|-----------|------------------------|
| 1 | **Physical noise extraction** | Turning microscopic, unpredictable fluctuations (quantisation noise, thermal noise, jitter, environmental noise) into raw bits — the entropy source of any TRNG. |
| 2 | **Differential / common-mode rejection** | XOR-ing two correlated channels so the shared (deterministic) part cancels and only independent noise survives. |
| 3 | **Randomness extractors & debiasing** | Post-processing (von Neumann debiasing, Toeplitz hashing, Leftover Hash Lemma) that removes bias **while preserving provable min-entropy** — different from hashing, which throws entropy away. |
| 4 | **Health testing & min-entropy estimation** | NIST SP 800-90B-style start-up/continuous tests and estimators that bound how much real entropy a source supplies, so a design can *discard* weak segments. |
| 5 | **Statistical randomness testing** | Test batteries (NIST SP 800-22, TestU01, Dieharder) used to *try to disprove* that the output is random. |
| 6 | **Keystream-based image encryption** | Using entropy bits as a one-time keystream (XOR + permutation + diffusion) and scoring it with NPCR, UACI, entropy, correlation and key-sensitivity analyses. |

---

## Slide 5 · Literature survey at a glance

**56 numbered references**: **51 journal papers**, 2 conference papers, 3 NIST standards
(plus 5 specifications listed as [S1]–[S5]). **40 of 56 (71%) are from 2021–2026**; the
rest are declared foundational/standards works.

| Theme | Papers | What it covers |
|---|---|---|
| **1 — Physical & acoustic entropy sources** | [1]–[21] | Where randomness physically comes from: acoustic/sensor, memristive, photonic/quantum, FPGA — plus what bioacoustics research tells us about bird audio. |
| **2 — Extraction, conditioning & validation** | [22]–[36] | Turning raw noise into usable bits, proving how much entropy is there, and testing the output (NIST, theory, ML-based attacks, hardware RNG designs). |
| **3 — Cryptographic applications & RNG security** | [37]–[56] | Image/audio encryption with random keystreams, the metrics used to score them, and the cryptanalysis that breaks them. |

**The one-sentence takeaway:** acoustic TRNGs are rare and music-based [1,2]; hardware TRNGs
need custom chips or dedicated sensors [3–15]; validation tooling exists but assumes a *stationary* source
[22,23,26]; application-layer encryption is usually driven by *algorithmic chaos* and keeps
getting broken [40,41,48]. **Nobody sits at the intersection** — that is our spot.

*(Slide 6 tables below are backup/handout: they are what the rubric's "comparison table"
requirement maps to.)*

---

## Slide 6 · Comparison tables (backup / handout)

### 6.1 Theme 1 — Physical & acoustic entropy sources

| Ref | Author(s), Year | Method | Dataset / Tools | Key finding | Limitation |
|---|---|---|---|---|---|
| [1] | Avaroğlu, Kahveci & Akkurt, 2024 | Acoustic TRNG; grey-wolf optimisation of threshold & sampling | MUSDB18 music; NIST 800-22 | Music is a viable entropy source | Music, not field audio; needs optimiser; single channel |
| [2] | Chai, Wu & Feng, 2024 | Sound + LDR sensor TRNG for blockchain PoS | Custom sensor rig | Acoustic/optical sensors can secure consensus | Needs a special rig; not commodity audio |
| [3] | Abellan et al., 2016 | Quantum entropy source on photonic IC | InP chip | Integrated QRNG is feasible | Application-specific fabrication |
| [4] | Wayne et al., 2010 | QRNG from photon arrival time intervals | Optical bench | Low bias at high speed | Dedicated optics; environmental sensitivity |
| [5] | Wang et al., 2024 | Compact QRNG: laser diode + hybrid Si chip | Photonic chip | Low-power quantum entropy | Still specialised hardware |
| [6] | Liu et al., 2024 | Conductance-noise TRNG in 1T′ MoTe₂ | 2D material device | Material-level stochastic entropy | Lab fabrication; not deployable in software |
| [7] | Pazos et al., 2023 | h-BN memristor + microcontroller TRNG | Memristor + MCU | Cheap MCU gives strong bits | Needs a fabricated memristor |
| [8] | Yu et al., 2024 | Random-telegraph-noise memristor TRNG | Memristor | RTN is a usable mechanism | Slow; device-level only |
| [9] | Abraham et al., 2022 | van-der-Waals heterojunction entropy source | 2D device | High-quality entropy source | Materials-lab setting |
| [10] | Hajduk et al., 2025 | Capacitive-oscillator jitter TRNG | FPGA | Compact, simple architecture | Needs FPGA fabric + calibration |
| [11] | Lu et al., 2025 | Ring-oscillator high-throughput TRNG | FPGA/ASIC | Very high throughput | Area & power; no software path |
| [12] | Matuszewski et al., 2024 | Low-complexity start–stop RO TRNG | FPGA | Lower resource use | Vendor/library dependence |
| [13] | Pawlowski et al., 2015 | On-board sensor entropy for constrained IoT | Light/accel sensors | Tiny RAM/Flash footprint | Sensor bias; hardware health tests; no audio |
| [14] | Cho et al., 2020 | Multi-sensor TRNG for drones | Mobile sensors | Robust across sensor types | Sample-rate limits |
| [15] | Zhang et al., 2023 | Heterogeneous entropy-source fusion | Sensor networks | Pooling raises robustness | Fusion complexity; no acoustic common-mode step |
| [16] | Ghani et al., 2023 | Global birdsong embeddings | Xeno-canto / BirdSet | Large open birdsong data exists | Classification focus; entropy never studied |
| [17] | Heinrich et al., 2025 | Interpretable DL bird-sound classifier | XCL, 9,734 species | Public bird audio is rich and large | Classification task; no randomness analysis |
| [18] | Briefer et al., 2010 | Song complexity via Shannon information | Field recordings | Entropy-style measures work on bird song | Biological, not cryptographic, framing |
| [19] | Tietze et al., 2024 | Song complexity vs. colourfulness trade-off | Large song corpus | Complexity quantified across species | Ecological focus; no signal-level bit analysis |
| [20] | Sawant et al., 2022 | Spectrogram cross-correlation for complexity | Recordings | Gives a complexity measure | Biology tooling, not security |
| [21] | Weiss et al., 2014 | Network analysis of vocal sequences | Recordings | Bird song has combinatorial structure | Descriptive; no entropy engineering |

### 6.2 Theme 2 — Extraction, conditioning & statistical validation

| Ref | Author(s), Year | Method | Dataset / Tools | Key finding | Limitation |
|---|---|---|---|---|---|
| [22] | Rukhin et al. (NIST), 2010 | SP 800-22 Rev. 1a: 15 statistical tests | NIST STS software | De-facto validation battery | Tests output, not the entropy of the source |
| [23] | Turan et al. (NIST), 2018 | SP 800-90B: health tests + min-entropy estimation | EA tool (IID/non-IID) | Bounds how much entropy a source really gives | Estimators assume stationarity/IID-like data |
| [24] | Barker & Kelsey (NIST), 2015 | SP 800-90A: DRBG mechanisms | Hash/CTR/HMAC-DRBG | Standard way to expand a good seed | Deterministic; needs a good seed, not a source |
| [25] | Luengo & García Villalba, 2023 | Independence of the 15 SP 800-22 tests | NIST STS | Tests overlap; two-level reading matters | Correct interpretation still under-used |
| [26] | Aslan et al., 2026 | Behaviour of SP 800-90B entropy estimators | EA tool | IID vs non-IID tracks disagree | No guidance for non-stationary audio |
| [27] | Stinson, 2002 | Universal hash families & Leftover Hash Lemma | Theory | Hashing can preserve min-entropy exactly | Theoretical; needs a uniform seed |
| [28] | Choi et al., 2023 | Practical entropy accumulation | Theory | Valid bound for accumulated output | Assumes independent blocks |
| [29] | Dang et al., 2025 | High-throughput extractor post-processing | TCHES hardware | Fast, provable extractors | Hardware; still post-processing |
| [30] | Crocetti et al., 2023 | Review of RNG assessment metrics | Survey | Maps statistical vs information-theoretic tests | Survey; no acoustic application |
| [31] | Li et al., 2020 | Deep-learning security verification of an NRNG | Deep learning | ML finds weaknesses tests miss | Attack-oriented; needs many samples |
| [32] | Truong et al., 2019 | ML cryptanalysis of a quantum RNG | LSTM | Environmental leakage can be learned | Side-channel issue, not a core QRNG flaw |
| [33] | Castillo et al., 2026 | Automated web framework for SP 800-22 | MDPI *IoT* | Reproducible testing made easy | Tooling; no new entropy method |
| [34] | Akter et al., 2025 | Lightweight hybrid RNG with entropy injection | FPGA (Cyclone V) | Low-resource RNG with health checks | FPGA-specific; not software/audio |
| [35] | Ahmed et al., 2024 | Race-hazard physical TRNG | ASIC/FPGA | Strong statistical quality | Hardware design complexity |
| [36] | Yilek et al., 2010 | Analysis of the 2008 Debian OpenSSL failure | Field study | Entropy failures break real systems at scale | Retrospective; motivates auditable sources |

### 6.3 Theme 3 — Cryptographic applications & RNG security

| Ref | Author(s), Year | Method | Dataset / Tools | Key finding | Limitation |
|---|---|---|---|---|---|
| [37] | Zhang et al., 2023 | Review of chaos-based image encryption | Survey | Maps the field, apps and challenges | Many schemes later broken |
| [38] | Alawida et al., 2023 | Chaos-based permutation for images | Simulation | Good diffusion & confusion | Chaos key handling; CPA concerns |
| [39] | Alghamdi, Munir & Ahmad, 2024 | Survey of image-encryption design & metrics | Survey | Fixes the standard metric set | Little attack analysis |
| [40] | Wang et al., 2018 | Chosen-plaintext attack on a 1D chaotic cipher | CPA | Scheme fully broken | Motivates plaintext-linked keystreams |
| [41] | Zhu, Sun et al., 2018 | Improved cryptanalysis of a chaos cipher | CPA | Key recovered from few plaintexts | "Security at build time" only |
| [42] | Zhu et al., 2023 | Fractional chaotic map + parallel DNA coding | Simulation | High throughput, good entropy | DNA-coding assumptions; key management |
| [43] | Kumar et al., 2024 | Chaos + elliptic curve + DNA for images | Simulation | Very large key space | Complexity; cryptanalysis still emerging |
| [44] | Güvenoğlu, 2024 | Multi-layered chaotic maps (Aizawa/Ricker/Sine-Circle/Chirikov) | Simulation | Simple, fast, good standard metrics | Deterministic chaos key; limited attack analysis |
| [45] | Alexan et al., 2025 | Chaotic systems + nonlinear transformations | Simulation | Strong entropy/NPCR on multi-image | Mostly statistical validation |
| [46] | Alrubaie et al., 2023 | 2D DNA encoding + 2D logistic map | Simulation | Fast, good diffusion | Chaos-derived key; CPA exposure |
| [47] | Chen et al., 2022 | Chaos + DNA for medical-image privacy | DICOM | Applied to real medical data | Needs secure key distribution |
| [48] | Vithayathil & Sreekumar, 2026 | CPA on permutation–substitution chaos ciphers | Chosen-plaintext | Whole family broken without the key | Confirms the pervasive CPA weakness |
| [49] | Nasr et al., 2024 | Chaos image/audio steganography | Simulation | Combines encryption and hiding | Hiding trade-offs; still chaos-based |
| [50] | Abdallah et al., 2022 | Multilayered audio encryption (tent-map) | Audio files | Block-cipher-like audio security | No true-randomness source |
| [51] | Sathiyamurthi & Ramakrishnan, 2017 | Chaotic-shift-keying speech encryption | Speech | High key sensitivity | Chaos-derived (algorithmic) keystream |
| [52] | Huang et al., 2025 | 3D chaotic speech encryption (Sine Hashing) | Speech | Efficient, noise-robust | Still algorithmic randomness |
| [53] | Castillo-García et al., 2026 | Chaotic high-speed random-bit generation | Simulation/FPGA | Very high bit rates | Chaos has a deterministic core |
| [54] | Wu et al., 2025 | Lightweight high-throughput hardware TRNG | ASIC/FPGA | Good throughput per area | Hardware only; no software path |
| [55] | Wu et al., 2025 | Neural-network pseudorandom generators | Deep learning | Cheap random-looking output | Pseudorandom, not physical; needs training |
| [56] | Panigrahi et al., 2025 | LSB steganographic image hiding | Simulation | High payload, imperceptible | Hiding ≠ randomness; no entropy guarantee |

---

## Slide 7 · In-depth study — six recent papers (2024–2026)

*Why this slide exists:* we read six current papers end-to-end, line our approach up against
them, and show the gap each one leaves. All six are journal papers from 2024–2026, and
authors are written out in full (no "et al.").

| # | Paper (full APA) | Their randomness source | Their validation | Gap we address |
|---|---|---|---|---|
| D1 | Avaroğlu, E., Kahveci, S., & Akkurt, R. (2024). *Traitement du Signal, 41*(2), 791–799. | Thresholded **music** tracks | NIST SP 800-22 after processing | Needs an optimiser, one channel, no source-level entropy figure |
| D2 | Akter, S., Williams, S., Kirtonia, P., Bayoumi, M. A., & Khalil, K. (2025). *IEEE Open Journal of Circuits and Systems, 6*, 257–269. | **Ring oscillators** on an FPGA | Health tests on hardware | Needs custom silicon; not auditable in software |
| D3 | Aslan, M., Doğanaksoy, A., Saygı, Z., Sönmez Turan, M., & Sulak, F. (2026). *Cryptography and Communications, 18*(1), 63–81. | — (estimator study, not a generator) | Analysis of SP 800-90B estimators | Estimators assume IID/stationary data; audio is not |
| D4 | Heinrich, R., Rauch, L., Sick, B., & Scholz, C. (2025). *Ecological Informatics, 87*, 103070. | — (bird-audio **classification**) | Accuracy on XCL (9,734 species) | Treats bird sound as a label problem, never as an entropy source |
| D5 | Alexan, W., El Shabasy, N. H., Ehab, N., & Maher, E. A. (2025). *Scientific Reports, 15*, 31246. | **5D chaotic map** from a fixed key | Entropy, NPCR, UACI, correlation | Keystream is deterministic, not physical |
| D6 | Vithayathil, A. J., & Sreekumar, A. (2026). *Journal of Computer Virology and Hacking Techniques, 22*(1). | — (attacks others' ciphers) | Chosen-plaintext attacks | Shows why algorithmic keystreams must not be trusted |

### D1 — the closest prior work (spend most of the time here)

**Avaroğlu, E., Kahveci, S., & Akkurt, R. (2024).** *Optimization of acoustic entropy source
for random sequence generation using an improved grey wolf algorithm.* Traitement du Signal,
41(2), 791–799.

- **They did:** took music files, thresholded the waveform to extract bits, and used an
  improved Grey Wolf optimiser to pick the threshold and sampling interval; checked the
  output with NIST SP 800-22.
- **Their gap:** (a) studio **music**, not natural field recordings; (b) the threshold has to be
  **re-optimised per recording** — not a fixed, reproducible pipeline; (c) **one channel** — no
  handling of stereo correlation; (d) no **min-entropy number for the raw source** and no
  discard-only health gate; (e) validation happens after processing, on the final bits.
- **Our answer:** fixed parameter-light pipeline on **bird field recordings** (free, non-stationary,
  available from Xeno-canto) → **stereo L⊕R common-mode rejection** → **three-view XOR extractor**
  → **health gate that throws away weak frames** → min-entropy reported **on the raw stream** →
  NIST SP 800-22 run **on the raw stream**, with **no hashing at any point**.

### D2 — hardware RNGs

**Akter, S., Williams, S., Kirtonia, P., Bayoumi, M. A., & Khalil, K. (2025).** *A lightweight
hybrid random number generator with dynamic entropy injection.* IEEE Open Journal of Circuits
and Systems, 6, 257–269.

- **They did:** a low-resource FPGA generator combining ring oscillators with "dynamic entropy
  injection", complete with health checks — a strong, well-tested design.
- **Their gap:** it only exists **inside an FPGA** (Cyclone V). You cannot inspect the bits after
  the fact, and devices without an FPGA — phones, Raspberry Pis, IoT sensors — get nothing.
- **Our answer:** same quality bar, **commodity hardware only**: CPU, microphone, open code. Every
  bit points back to a file position and a sample index, so the source is auditable by anyone.

### D3 — the standard for measuring entropy

**Aslan, M., Doğanaksoy, A., Saygı, Z., Sönmez Turan, M., & Sulak, F. (2026).** *Observations on
NIST SP 800-90B entropy estimators.* Cryptography and Communications, 18(1), 63–81.

- **They did:** compared the SP 800-90B estimators and showed the IID and non-IID tracks give
  noticeably different answers (the paper even carries a published correction).
- **Their gap:** the estimators assume the source is roughly **stationary / IID**. Bird recordings
  are the opposite — silence, tonal bursts, song-to-silence transitions. Nobody says what to do
  with the bad frames.
- **Our answer:** trim silence up front, run a **frame-level health gate that discloses how many
  frames were dropped**, estimate min-entropy **only on the surviving stream**, and state exactly
  which estimator track we used (IID, with the histogram estimator) so the number is reproducible.

### D4 — the bird-audio side

**Heinrich, R., Rauch, L., Sick, B., & Scholz, C. (2025).** *AudioProtoPNet: An interpretable
deep learning model for bird sound classification.* Ecological Informatics, 87, 103070.

- **They did:** a prototype-based deep network that classifies bird sounds across a corpus of
  9,734 species — good evidence that huge, varied public bird-audio data really exists.
- **Their gap:** they ask *"which species is this?"*, never *"how unpredictable is this audio?"*.
  Accuracy is reported; entropy is not.
- **Our answer:** we use the same class of open recordings and ask the missing question: **how many
  bits of real entropy per byte does this audio carry?** That is O1 of our objectives.

### D5 — how encryption is usually done (and why we don't)

**Alexan, W., El Shabasy, N. H., Ehab, N., & Maher, E. A. (2025).** *A secure and efficient
image encryption scheme based on chaotic systems and nonlinear transformations.* Scientific
Reports, 15, 31246.

- **They did:** multi-image encryption driven by a 5D chaotic system plus non-linear transforms,
  scoring well on entropy, NPCR, UACI and correlation.
- **Their gap:** the keystream comes from a **deterministic chaotic map started from a fixed key** —
  if the key (or part of it) leaks, the whole stream is reproducible. Their validation is
  **statistical only**: no chosen-plaintext / known-plaintext attack is run.
- **Our answer:** the keystream is **physical** and **used once per image**, and we report the same
  standard metrics **plus** key-sensitivity and a wrong-key control, so the result can be compared
  directly with theirs.

### D6 — why "chaos" keystreams are risky

**Vithayathil, A. J., & Sreekumar, A. (2026).** *Cryptanalysis of chaos-based image encryption
algorithms employing different permutation-substitution designs.* Journal of Computer Virology
and Hacking Techniques, 22(1).

- **They did:** chosen-plaintext attacks that recover the key of several permutation–substitution
  chaos ciphers **without knowing the key at all**.
- **Their message to us:** any scheme whose keystream is independent of the plaintext can be
  algebraically undone — publishing good NPCR/UACI numbers is not a proof of security.
- **Our answer:** reject algorithmic chaos as the **entropy source**; take the keystream from
  physical audio, never reuse it, and test sensitivity to both key and plaintext.

**Closing line for this slide:** *"Six recent papers, one shared blind spot — nobody validates an
unconditioned, physically-derived stream from natural audio. That is exactly what we build."*

---

## Slide 8 · Research gaps (6)

Each gap is drawn straight from the comparison tables in §6.

- **G1 — No auditable, conditioning-free randomness from commodity audio.**
  Physical-entropy work uses bespoke silicon (quantum/photonic [3–5], memristor & 2D materials
  [6–9], FPGA/ASIC [10–12]) or a cryptographic conditioner that makes the source irrelevant
  [24,29,34]. The few acoustic TRNGs [1,2] use music or custom rigs. *Gap: no pipeline that
  produces well-behaved bits from ordinary bird recordings **without any cryptographic
  conditioning**, so each bit stays attributable to a measurement.*

- **G2 — Correlated (common-mode) structure in stereo audio is ignored.**
  Sensor TRNGs sample a single channel [13–15]; acoustic work treats the signal as one stream [1].
  Stereo files share tonal content and decoder artefacts across channels, which adds bias when
  channels are simply concatenated. *Gap: no explicit **common-mode rejection** (channel XOR)
  step before extraction.*

- **G3 — Entropy estimation and health testing are weak for non-stationary natural audio.**
  SP 800-90B estimators assume stationarity [23,26], while field recordings are strongly
  non-stationary [16–18]. Existing lightweight TRNGs do have health checks — on hardware sources
  [34,35]. *Gap: a runtime health gate that **discards** weak frames (never transforms them) and
  still yields a defensible min-entropy number for non-stationary audio.*

- **G4 — Evaluation is inconsistent and usually done only after conditioning.**
  Many works report SP 800-22 on processed output, short sequences, or skip two-level
  interpretation [22,25,30]; some rely on ML to find weaknesses [31,32].
  *Gap: end-to-end, reproducible validation on **raw, unconditioned** bits with explicit
  thresholds and sequence lengths.*

- **G5 — Application security is built on algorithmic (chaos) keystreams that keep getting broken.**
  Chaos-based image/audio ciphers [37–47,49–53] report NPCR/UACI/entropy, yet chosen-plaintext
  attacks break them when the keystream does not depend on the plaintext [40,41,48].
  *Gap: a keystream that is genuinely physical and single-use, reported **together with**
  key- and plaintext-sensitivity analysis.*

- **G6 — Throughput and practicality are rarely benchmarked against standard baselines.**
  Sensor/acoustic works seldom state clean bits per second or compare against OS/PRNG/CSPRNG
  baselines [13,14,34]. *Gap: a quantified throughput (clean entropy bits/s) and a statistical
  comparison against `os.urandom` / AES-CTR DRBG.*

---

## Slide 9 · Objectives

> Written as measurable outcomes, not activities. Each maps back to a gap.

**Main objective:** design, implement and rigorously validate a TRNG whose randomness comes
**solely and verifiably** from the physical noise in bird-chirp recordings — **with no
cryptographic conditioning** — and demonstrate its usefulness by encrypting images with it.

| # | Objective (measurable outcome) | Target | Gap |
|---|---|---|---|
| **O1** | **Characterise the source:** defensible min-entropy estimate of the raw bitstream over a held-out set of recordings. | **≥ 7.5 bits/byte** (of 8.0) on the pooled raw stream, across ≥ 10 recordings/species | G1, G3 |
| **O2** | **Pass randomness testing on unconditioned output:** full NIST SP 800-22 battery on the raw bits. | **≥ 98% first-level pass** (p ≥ 0.01) on all 15 tests, sequences ≥ 1×10⁶ bits, two-level proportion ≥ 0.96 | G4 |
| **O3** | **Benchmark throughput & quality against baselines.** | Sustained **≥ 20 kbit/s** clean entropy (pool ≈ 32 kbit/s today), output statistically **indistinguishable** from `os.urandom`/AES-CTR DRBG (\|z\| < 3, autocorrelation < 0.02) | G6 |
| **O4** | **Image-encryption demo with accepted security metrics** using the audio keystream. | On 512×512 images: cipher entropy **≥ 7.99**, \|correlation\| **≤ 0.01**, **NPCR ≥ 99.6%**, UACI in 27–33%, byte-identical round trip, **≥ 99.6%** change under a wrong key | G5 |

**Scope note:** O1–O3 are the generator, O4 is the application. Review 1 presents literature,
gaps and objectives — **code is not required at this review** (it exists anyway:
`github.com/amorfati3735/audio-trng`).

---

## Slide 10 · NIST standards, test cases and metrics

### 10.1 The standards we build on

| Standard | What it governs | How we use it |
|---|---|---|
| **NIST SP 800-22 Rev. 1a** [22] | 15 statistical tests for bitstreams | Our **output** validation battery (run on raw bits) |
| **NIST SP 800-90B** [23] | Entropy-source design: health tests + min-entropy estimators | Our **source** health gate and min-entropy estimate |
| **NIST SP 800-90A Rev. 1** [24] | DRBG constructions (Hash/CTR/HMAC) | The **baseline** generator we benchmark against |
| **NIST SP 800-90C** [S3] | Random-bit-generator constructions (conditioning chain) | Defines what "conditioning" formally means — which we deliberately skip |
| **FIPS 140-3** [S1] | Cryptographic module security requirements | Why a validated entropy source must be health-tested at all |

### 10.2 The 15 test cases (SP 800-22) — what each one looks for

| # | Test | What it catches |
|---|---|---|
| 1 | Frequency (Monobit) | Overall balance of 0s and 1s |
| 2 | Frequency within a block | Bias inside small windows, not just globally |
| 3 | Runs | Too many/few transitions — a stuck or over-smooth stream |
| 4 | Longest run of ones in a block | Locally long streaks |
| 5 | Binary matrix rank | Linear dependencies among fixed-size blocks |
| 6 | Discrete Fourier Transform (spectral) | Periodic patterns hidden in the bitstream |
| 7 | Non-overlapping template matching | Repetitions of a fixed sub-pattern |
| 8 | Overlapping template matching | The same, with overlapping windows |
| 9 | Maurer's universal test | How well the stream compresses vs. an ideal one |
| 10 | Linear complexity | How cheap a LFSR would be to reproduce it |
| 11 | Serial | Any two- and three-bit sub-block bias |
| 12 | Approximate entropy | Correlation between consecutive blocks of length m |
| 13 | Cumulative sums | Whether a random walk drifts off centre |
| 14 | Random excursions | Frequency of visits to non-zero states in the walk |
| 15 | Random excursions variant | Same states, different counting rule |

**Pass criteria (two-level, as NIST prescribes):**
- **Level 1 — per sequence:** p-value ≥ α = 0.01 → sequence passes that test.
- **Level 2 — proportion:** pass rate must fall inside
  (1−α) ± 3·√(α(1−α)/n); for n = 100 sequences that is **≥ 0.96 and ≤ 1.00**.
- **Level 2 — uniformity:** p-values across sequences must themselves look uniform
  (chi-square on 10 bins, P_T ≥ 0.0001).
- All three are reported; a single number ("we passed 800-22") is not a result.

### 10.3 Health-test cases (SP 800-90B) — on the source, before any test

| Health test | Rule of thumb |
|---|---|
| **Repetition Count Test (RCT)** | Fail if the same 8-bit symbol repeats more than a run-length limit — catches a stuck ADC / silence |
| **Adaptive Proportion Test (APT)** | Fail if one symbol takes more than ~68% of a sliding window — catches a dominant (biased) byte |
| **Start-up tests** | Run once on power-up / file-load before any bit is accepted |
| **Min-entropy estimation** | Histogram/collision estimator on the IID track; the number that O1 reports |

### 10.4 Performance & correlation metrics we will report

| Group | Metric | What it tells you | Our target |
|---|---|---|---|
| **Throughput** | Raw bit rate (kbit/s) | Speed of the extractor | report as measured |
| | **Clean entropy rate** (kbit/s) | What survives the health gate | ≥ 20 kbit/s |
| | Yield (%) | % of frames that passed the gate | report per recording |
| | Bits per minute of audio | Practicality for a user | report |
| **Source quality** | Min-entropy (bits/byte) | Worst-case entropy of the raw stream | ≥ 7.5 / 8.0 |
| | Byte-uniformity (χ²) | Whether all 256 byte values are equally likely | p ≥ 0.01 |
| | Monobit \|s(n)\|/√n | Balance of ones and zeros | < 1.06 (p ≥ 0.01) |
| | Autocorrelation | Predictability across shifts | < 0.02 |
| **Test battery** | SP 800-22 pass proportion | Output indistinguishable from random | ≥ 98% (level 1), ≥ 0.96 (level 2) |
| | p-value uniformity (χ²) | Tests are not gamed by a lucky stream | P_T ≥ 0.0001 |
| **Baseline correlation** | z-test vs `os.urandom` / AES-CTR DRBG | Our stream behaves like a standard CSPRNG on the same tests | \|z\| < 3 for every test |
| **Encryption** | Information entropy of ciphertext | Ciphertext looks flat (max 8.0) | ≥ 7.99 |
| | **Pearson correlation** plain↔cipher | Statistical link broken by encryption | \|r\| ≤ 0.01 |
| | **NPCR** | % of pixels changed by a 1-pixel plaintext change (differential security) | ≥ 99.6% |
| | **UACI** | Average intensity change of that perturbation | 27–33% (ideal 33.46%) |
| | Key sensitivity | Wrong key ⇒ completely different image | ≥ 99.6% pixels differ |
| | Round-trip identity | Correct key ⇒ exact original | byte-identical |

**How the numbers are expected to correlate (say this in one breath):** raising the health-gate
threshold should *raise* min-entropy and SP 800-22 pass rates while *lowering* throughput —
that trade-off curve is the honest result we will plot, together with plain-vs-cipher
correlation scatter plots and a side-by-side table of our stream against `os.urandom`.

*Figure: `diagrams/fig5_validation_results.png`.*

---

## Slide 11 · Expected outcome & what's next

- **What exists today:** an open, CPU-only pipeline that converts bird recordings into
  validated, unconditioned random bits and encrypts/decrypts images with them
  (`github.com/amorfati3735/audio-trng`). Metrics and figures are in `README.md`.
- **Outcome we are aiming for (BACSE291 Outcome Analysis):**
  - **Publication in a Scopus-indexed journal** — *Published / Accepted for publication*,
    *Under review*, or *Communicated*;
  - **and/or Publication in a Scopus-indexed conference** — *Paper presented* or *Communicated*;
  - **and/or Patent** — *Patent published*, *Patentability Search Result – Approved*, or
    *Patent IDF submitted* (complete provisional specification draft).
- **Proof of outcome required at the Final Review** (Student Guidelines): acceptance email /
  submission ID / manuscript in the venue template for the publication track; filed application
  number / complete provisional specification draft for the patent track.
- **Next (Review 2, January 2027):** 60% implementation + complete system design —
  project plan, analysis & requirements, system design, proposed methodology.

---

## References (APA 7th) — handout

*Numbered [1]–[56]: **51 journal papers**, 2 conference papers ([2], [36]), and 3 NIST
standards ([22]–[24]); specifications [S1]–[S5] are listed after. A dagger (†) marks a
confirmed DOI/venue whose **page range or article number still needs checking** against the
publisher record. Entries still written "et al." need their full author list completed in
APA style before the final report (20-author limit).*

### Theme 1 — Physical & acoustic entropy sources

[1] Avaroğlu, E., Kahveci, S., & Akkurt, R. (2024). Optimization of acoustic entropy source for random sequence generation using an improved grey wolf algorithm. *Traitement du Signal, 41*(2), 791–799. https://doi.org/10.18280/ts.410220

[2] Chai, H., Wu, J., Feng, X., et al. (2024). Sound-LDR sensors empowered secure true random number generator for PoS consensus in blockchain. In *2024 IEEE 10th Conference on Big Data Security on Cloud (BigDataSecurity)* (pp. 139–144). IEEE.

[3] Abellan, C., Amaya, W., Jofre, M., et al. (2016). Quantum entropy source on an InP photonic integrated circuit for random number generation. *Optica, 3*(9), 989–994. https://doi.org/10.1364/OPTICA.3.000989

[4] Wayne, M. A., Jeffrey, E. R., Akselrod, G. M., & Kwiat, P. G. (2010). Low-bias high-speed quantum random number generator via shaped optical pulses. *Optics Express, 18*(9), 9351–9357. https://doi.org/10.1364/OE.18.009351

[5] Wang, X., et al. (2024). Compact quantum random number generator based on a laser diode and a hybrid silicon chip. *Photonics, 11*(5), 468. https://doi.org/10.3390/photonics11050468

[6] Liu, Y., et al. (2024). Harnessing physical entropy noise in structurally metastable 1T′ molybdenum ditelluride. *Nano Letters, 24*(45), 14315–14321. https://doi.org/10.1021/acs.nanolett.4c03848 †

[7] Pazos, S., et al. (2023). Hardware implementation of a true random number generator based on h-BN memristors. *Nanoscale, 15*(5), 2171–2180. https://doi.org/10.1039/D2NR04758E †

[8] Yu, D., et al. (2024). True random number generator using stochastic noise in memristors. *Chaos, Solitons & Fractals, 189*, 115172. https://doi.org/10.1016/j.chaos.2024.115172 †

[9] Abraham, N., et al. (2022). A high-quality entropy source using a van der Waals heterojunction for true random number generation. *ACS Nano, 16*(4), 5898–5908. https://doi.org/10.1021/acsnano.1c11084 †

[10] Hajduk, Z., et al. (2025). Simple true random number generator using capacitive oscillators. *Electronics, 14*(21), 4228. https://doi.org/10.3390/electronics14214228

[11] Lu, Y., et al. (2025). High-throughput true random number generator based on ring oscillators. *Microelectronics Journal, 161*, 106637. https://doi.org/10.1016/j.mejo.2025.106637 †

[12] Matuszewski, Ł., et al. (2024). A low-complexity start–stop true random number generator for FPGAs. *International Journal of Electronics and Telecommunications*. †

[13] Pawlowski, M. P., et al. (2015). Harvesting entropy for random number generation for Internet of Things constrained devices using on-board sensors. *Sensors, 15*(10), 26838–26865. https://doi.org/10.3390/s151026838

[14] Cho, S. M., et al. (2020). Random number generator using sensors for drone. *IEEE Access, 8*, 33533–33542. https://doi.org/10.1109/ACCESS.2020.2974076 †

[15] Zhang, J., et al. (2023). Random number generation based on heterogeneous entropy sources fusion in multi-sensor networks. *Sensors, 23*(20), 8497. https://doi.org/10.3390/s23208497

[16] Ghani, B., et al. (2023). Global birdsong embeddings enable superior transfer learning for bioacoustic classification. *Scientific Reports, 13*, 20914. https://doi.org/10.1038/s41598-023-47970-4 †

[17] Heinrich, R., Rauch, L., Sick, B., & Scholz, C. (2025). AudioProtoPNet: An interpretable deep learning model for bird sound classification. *Ecological Informatics, 87*, 103070. https://doi.org/10.1016/j.ecoinf.2025.103070

[18] Briefer, E., et al. (2010). Are bird song complexity and song sharing shaped by habitat structure? *Journal of Theoretical Biology, 262*(1), 151–164. https://doi.org/10.1016/j.jtbi.2009.09.020 †

[19] Tietze, D. T., et al. (2024). Trade-off between song complexity and colorfulness in birds. *Diversity, 16*(6), 332. https://doi.org/10.3390/d16060332

[20] Sawant, S., et al. (2022). Spectrogram cross-correlation can be used to measure the complexity of bird vocalizations. *Methods in Ecology and Evolution, 13*(2), 475–486. https://doi.org/10.1111/2041-210X.13765 †

[21] Weiss, M., et al. (2014). The use of network analysis to study complex animal communication systems. *PLoS ONE, 9*(4), e94726. https://doi.org/10.1371/journal.pone.0094726

### Theme 2 — Extraction, conditioning & statistical validation

[22] Rukhin, A., Soto, J., Nechvatal, J., et al. (2010). *A statistical test suite for random and pseudorandom number generators for cryptographic applications* (NIST Special Publication 800-22 Rev. 1a). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-22r1a

[23] Turan, M. S., Barker, E., Kelsey, J., McKay, K. A., Baish, M. L., & Boyle, M. (2018). *Recommendation for the entropy sources used for random bit generation* (NIST Special Publication 800-90B). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-90B

[24] Barker, E., & Kelsey, J. (2015). *Recommendation for random number generation using deterministic random bit generators* (NIST Special Publication 800-90A Rev. 1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-90Ar1

[25] Luengo, E. A., & García Villalba, L. J. (2023). Further analysis of the statistical independence of the NIST SP 800-22 randomness tests. *Applied Mathematics and Computation, 456*, 128162. https://doi.org/10.1016/j.amc.2023.128162 †

[26] Aslan, M., Doğanaksoy, A., Saygı, Z., Sönmez Turan, M., & Sulak, F. (2026). Observations on NIST SP 800-90B entropy estimators. *Cryptography and Communications, 18*(1), 63–81. https://doi.org/10.1007/s12095-025-00778-7 *(erratum: 18, 83–84)*

[27] Stinson, D. R. (2002). Universal hash families and the leftover hash lemma, and applications to cryptography and computing. *Journal of Combinatorial Mathematics and Combinatorial Computing, 42*, 3–31. †

[28] Choi, Y., et al. (2023). Practical entropy accumulation for random number generators. *Entropy, 25*(7), 1056. https://doi.org/10.3390/e25071056 †

[29] Dang, Y., Grujić, M., Yang, B., Zhu, W., Wang, H., Zhu, M., Verbauwhede, I., & Liu, L. (2025). Entropy extractor based high-throughput post-processings for True Random Number Generators. *IACR Transactions on Cryptographic Hardware and Embedded Systems, 2025*(4), 1–26.

[30] Crocetti, L., et al. (2023). Review of methodologies and metrics for assessing the quality of random number generators. *Electronics, 12*(3), 723. https://doi.org/10.3390/electronics12030723

[31] Li, C., et al. (2020). Deep learning-based security verification for a random number generator. *IEEE Access, 8*, 170609–170621. https://doi.org/10.1109/ACCESS.2020.3024757 †

[32] Truong, N. D., Haw, J. Y., Assad, S. M., Lam, P. K., & Kavehei, O. (2019). Machine learning cryptanalysis of a quantum random number generator. *IEEE Transactions on Information Forensics and Security, 14*(2), 403–410. https://doi.org/10.1109/TIFS.2018.2850771

[33] Castillo, J., et al. (2026). Automated framework for testing random number generators for IoT security applications using NIST SP 800-22. *IoT, 7*(1), 26. https://doi.org/10.3390/iot7010026 †

[34] Akter, S., Williams, S., Kirtonia, P., Bayoumi, M. A., & Khalil, K. (2025). A lightweight hybrid random number generator with dynamic entropy injection. *IEEE Open Journal of Circuits and Systems, 6*, 257–269. https://doi.org/10.1109/OJCAS.2025.3564409

[35] Ahmed, H. O., et al. (2024). A true random number generator based on race hazard. *IEEE Access, 12*, 142862–142873. https://doi.org/10.1109/ACCESS.2024.3461788 †

[36] Yilek, S., Rescorla, E., Shacham, H., Enright, B., & Savage, S. (2010). When private keys are public: Results from the 2008 Debian OpenSSL vulnerability. In *Proceedings of the 9th ACM SIGCOMM Conference on Internet Measurement (IMC '10)* (pp. 15–27). ACM. https://doi.org/10.1145/1879141.1879144

### Theme 3 — Cryptographic applications & RNG security

[37] Zhang, B., et al. (2023). Chaos-based image encryption: Review, application, and challenges. *Mathematics, 11*(11), 2585. https://doi.org/10.3390/math11112585

[38] Alawida, M., et al. (2023). A novel chaos-based permutation for image encryption. *Journal of King Saud University – Computer and Information Sciences, 35*(6), 101595. https://doi.org/10.1016/j.jksuci.2023.101595 †

[39] Alghamdi, Y., Munir, M., & Ahmad, J. (2024). Image encryption algorithms: A survey of design and evaluation metrics. *Journal of Cybersecurity and Privacy, 4*(1), 7. https://doi.org/10.3390/jcp4010007

[40] Wang, H., et al. (2018). Cryptanalysis and enhancements of image encryption using combination of the 1D chaotic map. *Signal Processing, 144*, 444–452. https://doi.org/10.1016/j.sigpro.2017.11.005 †

[41] Zhu, C., Sun, K., et al. (2018). Improved cryptanalysis and enhancements of an image encryption scheme. *Entropy, 20*(11), 843. https://doi.org/10.3390/e20110843

[42] Zhu, S., et al. (2023). Image encryption scheme based on newly designed chaotic map and parallel DNA coding. *Mathematics, 11*(1), 231. https://doi.org/10.3390/math11010231

[43] Kumar, S., et al. (2024). A chaotic based image encryption scheme using elliptic curve cryptography and DNA sequences. *Artificial Intelligence Review, 57*, 108. https://doi.org/10.1007/s10462-024-10719-0 †

[44] Güvenoğlu, E. (2024). An image encryption algorithm based on multi-layered chaotic maps and its security analysis. *Connection Science, 36*(1), 2312108. https://doi.org/10.1080/09540091.2024.2312108

[45] Alexan, W., El Shabasy, N. H., Ehab, N., & Maher, E. A. (2025). A secure and efficient image encryption scheme based on chaotic systems and nonlinear transformations. *Scientific Reports, 15*, 31246. https://doi.org/10.1038/s41598-025-15794-z

[46] Alrubaie, A. H., et al. (2023). Image encryption based on 2DNA encoding and chaotic 2D logistic map. *Journal of Engineering and Applied Science, 70*, 76. https://doi.org/10.1186/s44147-023-00228-2 †

[47] Chen, L., et al. (2022). Security measurement of a medical communication scheme based on chaos and DNA coding. *Journal of Visual Communication and Image Representation, 82*, 103404. https://doi.org/10.1016/j.jvcir.2021.103404 †

[48] Vithayathil, A. J., & Sreekumar, A. (2026). Cryptanalysis of chaos-based image encryption algorithms employing different permutation-substitution designs. *Journal of Computer Virology and Hacking Techniques, 22*(1). https://doi.org/10.1007/s11416-026-00634-z †

[49] Nasr, M. A., et al. (2024). A robust audio steganography technique based on image encryption and chaos maps. *Scientific Reports, 14*. https://doi.org/10.1038/s41598-024-73353-x †

[50] Abdallah, H. A., et al. (2022). A multilayered audio signal encryption approach for secure voice communication. *Electronics, 12*(1), 2. https://doi.org/10.3390/electronics12010002

[51] Sathiyamurthi, P., & Ramakrishnan, S. (2017). Speech encryption using chaotic shift keying for secured speech communication. *EURASIP Journal on Audio, Speech, and Music Processing, 2017*, 20. https://doi.org/10.1186/s13636-017-0118-0

[52] Huang, Y., et al. (2025). A 3D robust chaotic speech encryption scheme based on Sine Hashing. *Journal of Information Security and Applications, 92*, 104024. https://doi.org/10.1016/j.jisa.2025.104024 †

[53] Castillo-García, I. S., et al. (2026). High-speed random bit generation based on a chaotic system. *Electronics, 15*(9), 1917. https://doi.org/10.3390/electronics15091917 †

[54] Wu, S., et al. (2025). Lightweight high-throughput true random number generator. *Microelectronics Journal, 157*, 106605. https://doi.org/10.1016/j.mejo.2025.106605 †

[55] Wu, X., et al. (2025). Pseudorandom number generators based on neural networks. *Journal of Reliable Intelligent Environments*. https://doi.org/10.1007/s44443-025-00007-4 †

[56] Panigrahi, R., et al. (2025). An effective steganographic technique for hiding the image using least significant bit substitution. *e-Prime – Advances in Electrical Engineering, Electronics and Energy, 11*, 100872. https://doi.org/10.1016/j.prime.2025.100872 †

### Standards, recommendations & specifications

[S1] National Institute of Standards and Technology. (2019). *Security requirements for cryptographic modules* (FIPS PUB 140-3). https://doi.org/10.6028/NIST.FIPS.140-3

[S2] International Telecommunication Union. (2019). *Quantum noise random number generator architecture* (ITU-T Recommendation X.1702). ITU.

[S3] Barker, E., Kelsey, J., et al. (2024). *Recommendation for random bit generator (RBG) constructions* (NIST Special Publication 800-90C, 4th public draft). NIST. https://doi.org/10.6028/NIST.SP.800-90C.4pd

[S4] National Institute of Standards and Technology. (2024). *Entropy source validation (ESV) programme* — SP 800-90B Entropy Assessment tool. https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations

[S5] NIST. (2016). *Random Bit Generation project overview*. https://csrc.nist.gov/projects/random-bit-generation

> **Standards note.** [22] SP 800-22 is our validation battery, [23] SP 800-90B is the basis of
> the source-health gate, [24] SP 800-90A is the DRBG baseline we benchmark against. They are
> specifications, not journal papers, and are counted separately so the ">50 journal papers"
> claim is not inflated.

---

## Appendix A — Rubric self-check

| Rubric indicator (5 marks each) | Requirement for full marks | Where addressed | Status |
|---|---|---|---|
| Understanding of the domain & key concepts | Comprehensive grasp of domain, concepts, terminology | Slides 2–4, plus the vocabulary in `Review1_speaker_notes.md` | 🟢 Covered |
| Review of journal articles, logically classified | **> 50 journal papers** | §6 — **51 journal papers** (+2 conference, +3 NIST standards), grouped in 3 themes | 🟢 Exceeds |
| Identification of research gaps | **Minimum 5 gaps** | §8 — **six gaps (G1–G6)**, each tied to specific refs | 🟢 Exceeds |
| Relevant & realistic objectives | Relevant, realistic, measurable | §9 — main objective + **O1–O4** with numeric targets | 🟢 Covered |
| *Guideline:* ≥70% papers from last 5 years | 2021–2026 dominant; older allowed if foundational and stated | **40 of 56 (71%) are 2021–2026** (75% if the 3 NIST standards are excluded); the 16 older works are declared foundational/normative below | 🟢 Met |

**Foundational / seminal / standards works (pre-2021, declared per the guideline):** quantum
entropy on a photonic IC [3]; photon-timing QRNG [4]; sensor-entropy pioneers [13,14];
avian-sound corpora & song analysis [18,21]; NIST SP 800-22/90A/90B [22–24]; the Leftover Hash
Lemma [27]; deep-learning RNG verification [31,32]; the Debian OpenSSL RNG failure [36];
chaos-cipher cryptanalyses [40,41]; chaotic speech encryption [51]. Every one is a recognised
foundational or normative work, not a recent result.

**Survey/review papers removed in this revision** (their "Dataset/Tools" column was simply
"Survey"): Cao et al. (2022), Gong et al. (2019), Herrero-Collantes & Garcia-Escartin (2017),
Zhao et al. (2024), Chai et al. (2025), Sharma, Naz & Shah (2026), plus conference/ePrint items
that added no method — total 16 references removed (72 → 56): 6 journal surveys/reviews and 10 conference/ePrint items. Three recent reviews are kept
because each *defines* a theme: [30] RNG metrics, [37] chaos image encryption, [39]
image-encryption evaluation metrics.

## Appendix B — Open items before submission

- Fill `[PROJECT ID]`, `[Name n]`, `[Reg No n]`, `[Guide Name]`, `[Designation]`.
- Verify every **†** page range / article number against the publisher record.
- Complete author lists still written "et al." (APA 7 lists up to 20 authors).
- Decide the primary outcome track (journal / conference / patent) with the guide and record
  the submission ID or application number as soon as it exists — that is the Final Review's
  "proof of outcome".

---

*Slide source for the Review 1 panel presentation. Companion: `Review1_speaker_notes.md`
(terminology, timing, Q&A). Full-length original: `Review1_audio_trng.md`.*
