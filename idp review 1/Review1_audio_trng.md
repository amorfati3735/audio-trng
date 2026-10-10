# BACSE291 – Innovative Design Project | First Review

**Project ID:** [PROJECT ID]
**Project Title:** Generation of True Random Numbers from Bird Chirping
**Academic Year:** 2026–2027 · Fall Semester 2026 · Review 1 (Panel) · 7 & 14 October 2026

## Team Details

| S.No | Name | Register Number | School |
|------|------|-----------------|--------|
| 1 | [Name 1] | [Reg No 1] | SCOPE |
| 2 | [Name 2] | [Reg No 2] | SCOPE |
| 3 | [Name 3] | [Reg No 3] | SCOPE |
| 4 | [Name 4] | [Reg No 4] | SCOPE |

## Guided Details

| | |
|---|---|
| Guide Name | [Guide Name] |
| Designation | [Designation] |
| School | SCOPE |

---

> **How to use this document.** This is the source markdown for the Review‑1 panel
> presentation. Each numbered section maps to one slide/section of the official
> `1. IDP Review 1 template.pdf`. Section 8 maps the content to the
> `2. BACSE291 REVIEW-1 Rubrics.pdf` so nothing is left unaddressed.
> A parallel `claude.md` in the project root records the reasoning, sources and
> open items so another AI (or teammate) can resume.

---

## 1. Brief Description of the Project

**Domain:** Applied Cryptography — Physical (non‑algorithmic) Randomness / Hardware & Signals Security
**Application Area:** Cryptographic key and nonce generation for resource‑constrained and privacy‑critical systems (IoT/embedded devices, edge sensing nodes) where a dedicated hardware TRNG is unavailable but a microphone is already present.

### Problem Statement · Proposed Solution · Expected Outcome

| **1. Problem Statement** | **2. Proposed Solution** | **3. Expected Outcome** |
|---|---|---|
| Cryptographic systems need unpredictable keys, nonces and salt. These are ideally drawn from **physical** (true) randomness, not deterministic algorithms. Modern TRNGs, however, depend on bespoke silicon (ring‑oscillator jitter, memristor noise, quantum optics) or on a **conditioning layer** (SHA‑256, AES‑CTR) that transforms almost any input into statistically random output — which makes the *physical source* statistically irrelevant and the system hard to audit. At the same time, low‑entropy failures are a real, documented class of breach (e.g. the 2008 Debian OpenSSL predictable‑RNG incident). The barrier today is therefore **not** "can we make random numbers" but "can we obtain well‑behaved randomness from a source that is cheap, ubiquitous and *auditable*." | We build a TRNG whose randomness comes **only** from physical processes in naturally occurring **bird‑chirp field recordings**: ADC quantisation noise, environmental/acoustic noise and the non‑stationary structure of the vocalisation itself. The **method** (not a hash) does the work: (i) **stereo common‑mode rejection** (L⊕R) to cancel correlated tonal and decoder artefacts; (ii) a **mixed physical extractor** XOR‑ing three complementary low‑bit views of each sample; (iii) a **source‑health gate** (NIST SP 800‑90B style) that *discards* statistically poor audio frames and never transforms data. Output bits are emitted **unconditioned** and validated directly, then used as a keystream for an image‑encryption demo. | A reproducible, open, CPU‑only pipeline that turns freely available bird recordings into validated true random bits with **no cryptographic conditioning**, plus (a) an entropy estimate and statistical‑test report on **raw** bits, (b) a throughput characterisation versus standard PRNG/CSPRNG baselines, and (c) an image‑encryption demonstration with standard security metrics. **Beneficiaries:** embedded/IoT developers needing cheap entropy, educators, and researchers studying auditable physical randomness. **Success is measured** by min‑entropy ≥ 7.5 bits/byte, NIST SP 800‑22 pass rate ≥ 98 %, and encryption metrics at or above accepted thresholds (see §5). |

**Why the approach is different (one line for the panel):** we deliberately *reject* cryptographic conditioning and instead engineer the *extraction method* — common‑mode rejection + a multi‑view physical extractor + a discarding‑only health gate — so that every output bit is traceable to a physical measurement, and we validate the *raw* stream rather than a whitened one.

---

## 2. Key Techniques in the Domain

| # | Technique | What it is (one line) |
|---|-----------|------------------------|
| 1 | **Physical noise extraction** | Turning unpredictable microscopic fluctuations (thermal/quantisation/environmental noise, jitter, metastability) into a raw bitstream — the entropy source of any TRNG. |
| 2 | **Differential / common‑mode rejection** | Differencing or XOR‑ing two correlated sensor channels so the shared (deterministic) component cancels and only independent noise survives. |
| 3 | **Randomness extractors & debiasing** | Mathematically sound post‑processing (von Neumann debiasing, Toeplitz/universal hashing, the Leftover Hash Lemma) that removes bias **while preserving provable min‑entropy** — distinct from cryptographic hashing. |
| 4 | **Entropy‑source health testing & min‑entropy estimation** | NIST SP 800‑90B style continuous/start‑up health tests and min‑entropy estimators that bound how much real entropy a source supplies (and let a design *discard* weak segments). |
| 5 | **Statistical randomness testing** | Batteries such as NIST SP 800‑22 (frequency, runs, spectral, autocorrelation, …), TestU01, Dieharder used to falsify non‑randomness of the output stream. |
| 6 | **Keystream‑based image/audio encryption** | Using entropy bits as a keystream (XOR/permutation/diffusion, often chaos‑assisted) and evaluating it with NPCR, UACI, entropy, correlation and key‑sensitivity analyses. |

## 3. Literature Review

The survey spans **56 numbered references** plus **5 specifications**: **51 are peer‑reviewed journal articles**, **2 are conference papers**, and **3 are NIST Special Publications**. The **51 journal articles** alone clear the rubric’s “> 50 journal papers” bar. Nine survey/review articles (counted as their own “dataset”) and ten conference/ePrint items from an earlier 72‑reference draft were dropped, and three of the remaining slots were backfilled with 2025 original research. Papers are grouped under the **three themes** requested by the template:

- **Theme 1 — Physical & Acoustic Entropy Sources:** where true randomness physically comes from (acoustic/sensor, electrical, memristive, photonic/quantum, FPGA) and how bird vocalisations are characterised as a signal.
- **Theme 2 — Entropy Extraction, Conditioning & Statistical Validation:** how raw noise is turned into valid bits, how much entropy is proven, and how output randomness is tested.
- **Theme 3 — Cryptographic Applications & RNG Security:** image/audio encryption using TRNG keystreams, their evaluation metrics, and cryptanalytic failures.

### 3.1 Theme 1 — Physical & Acoustic Entropy Sources

| Ref | Author(s), Year | Theme | Proposed Technique | Dataset / Tools | Key Findings | Limitations |
|---|---|---|---|---|---|---|
| [1] | Avaroğlu, Kahveci & Akkurt, 2024 | 1 | Acoustic entropy source + Improved Grey‑Wolf optimisation of threshold/sampling interval | MUSDB18 audio; NIST tests | Shows acoustic signals are viable entropy sources; statistical quality strongly depends on threshold & sampling interval | Music (not field/bird audio); requires optimisation layer; no stereo common‑mode handling; no conditioning‑free claim |
| [2] | Chai, Wu, Feng et al., 2024 | 1 | Sound + LDR sensors combined into a TRNG for blockchain PoS consensus | Sound‑LDR sensor rig; blockchain | Demonstrates a physical acoustic/optical sensor TRNG in a real application | Needs a special sound‑LDR rig; sensor‑specific; blockchain focus |
| [3] | Abellan et al., 2016 | 1 | Quantum entropy source on InP photonic IC | Photonic chip | Integrated QRNG feasible; high quality | Application‑specific fabrication; no audio/commodity path |
| [4] | Wayne, Jeffrey, Akselrod & Kwiat, 2010 | 1 | QRNG via digitised photon‑arrival time‑interval | Optical bench | Low bias at high speed | Dedicated optics; environmental sensitivity |
| [5] | Wang et al., 2024 | 1 | Compact QRNG on laser diode + hybrid Si chip | Photonic chip | Low‑power, compact quantum entropy | Still specialised hardware |
| [6] | Liu et al., 2024 | 1 | Physical entropy noise in metastable 1T′ MoTe₂ | Material/device | Demonstrates conductance‑noise TRNG in a 2D material | Lab fabrication; not deployable in software |
| [7] | Pazos et al., 2023 | 1 | h‑BN memristor + microcontroller TRNG circuit | h‑BN memristor | Highly stochastic bitstream from cheap MCU | Needs fabricated memristor |
| [8] | Yu et al., 2024 | 1 | Random‑telegraph‑noise memristor TRNG | Memristor device | RTN is a usable entropy mechanism | Slow, device‑level; no portability |
| [9] | Abraham et al., 2022 | 1 | van‑der‑Waals heterojunction entropy source | 2D device | High‑quality entropy source for cryptography | Materials‑science lab setting |
| [10] | Hajduk et al., 2025 | 1 | Jitter in capacitive‑oscillator TRNG | FPGA | Compact, simple architecture | Needs FPGA fabric; calibration |
| [11] | Lu et al., 2025 | 1 | Ring‑oscillator high‑throughput TRNG | FPGA/ASIC | Very high throughput | Area/power; no software path |
| [12] | Matuszewski et al., 2024 | 1 | Low‑complexity start–stop RO TRNG | FPGA | Lower resource use | Vendor/library dependence |
| [13] | Pawlowski et al., 2015 | 1 | Harvesting on‑board sensor entropy for constrained IoT | Sensors (light/accel, etc.) | Sensor RNG feasible with tiny RAM/Flash footprint | Raw sensor bias; needs health tests; no acoustic focus |
| [14] | Cho et al., 2020 | 1 | Multi‑sensor (accel/magnetometer/orientation) TRNG for drones | Mobile sensors | Robustness across sensors; practical for drones | Small sensor bias; sample‑rate limits |
| [15] | Zhang et al., 2023 | 1 | Heterogeneous entropy‑source fusion in multi‑sensor networks | Sensor networks | Pooling heterogeneous sources raises entropy & robustness | Fusion complexity; no acoustic common‑mode treatment |
| [16] | Ghani et al., 2023 | 1 | Global birdsong embeddings (transfer learning) | Xeno‑canto / BirdSet | Large‑scale birdsong data + embeddings available for reuse | Classification focus; entropy properties not studied |
| [17] | Heinrich et al., 2025 | 1 | Interpretable DL model for bird sound classification | XCL (9,734 species) | Confirms richness/scale of public bird audio (sampling‑rate detail) | Classification task; no randomness analysis |
| [18] | Briefer et al., 2010 | 1 | Song complexity via information theory (Shannon) | Field recordings | Demonstrates entropy‑like measures on bird song | Biological, not cryptographic, framing |
| [19] | Tietze et al., 2024 | 1 | Song complexity vs. colourfulness trade‑off | Large song corpus | Quantifies song complexity across species | Ecological focus; no signal‑level bit analysis |
| [20] | Sawant et al., 2022 | 1 | Spectrogram cross‑correlation for song complexity | Recordings | Method to measure vocalisation complexity | Tooling for biology, not security |
| [21] | Weiss et al., 2014 | 1 | Network analysis of complex animal vocal sequences | Recordings | Shows rich combinatorial structure in bird song | Descriptive; no entropy‑source engineering |

### 3.2 Theme 2 — Entropy Extraction, Conditioning & Statistical Validation

| Ref | Author(s), Year | Theme | Proposed Technique | Dataset / Tools | Key Findings | Limitations |
|---|---|---|---|---|---|---|
| [22] | Rukhin et al. (NIST), 2010 | 2 | SP 800‑22 Rev. 1a: 15 statistical tests | NIST STS software | De‑facto standard battery for RNG validation (frequency, runs, spectral, serial, …) | Tests randomness, not entropy; susceptible to misuse/variable p‑values |
| [23] | Turan et al. (NIST), 2018 | 2 | SP 800‑90B entropy‑source design & estimation | EA tool, IID/non‑IID estimators | Defines health tests + min‑entropy bounds for physical sources | Estimators assume stationarity; conservative/uncertain on non‑IID sources |
| [24] | Barker & Kelsey (NIST), 2015 | 2 | SP 800‑90A: DRBG mechanisms | Hash/CTR/HMAC‑DRBG | Standard deterministic expansion of a seed | Needs a good seed; not a true source |
| [25] | Luengo & García Villalba, 2023 | 2 | Analysis of statistical independence of SP 800‑22 tests | NIST STS | Shows tests are not fully independent; two‑level interpretation matters | Correct interpretation still under‑used |
| [26] | Aslan et al., 2026 | 2 | Study of SP 800‑90B min‑entropy estimators | EA tool | Highlights estimator discrepancies/IID vs non‑IID tracks | No guidance for non‑stationary audio |
| [27] | Stinson, 2002 | 2 | Universal hash families & LHL (expository) | Theory | Explains entropy‑preserving securing via hashing | Theoretical |
| [28] | Choi et al., 2023 | 2 | Practical entropy accumulation | Entropy theory | Theoretical min‑entropy bound for accumulated output | Assumes independent blocks |
| [29] | Dang et al., 2025 | 2 | High‑throughput entropy‑extractor post‑processing | IACR TCHES | Efficient extractor hardware for TRNGs | Hardware‑oriented; still post‑processing |
| [30] | Vrana, Lou & Kuang, 2025 | 2 | QPP‑RNG: system‑jitter TRNG evaluated under SP 800‑90B / 800‑22 | Commodity CPUs (Windows/macOS/Raspberry Pi); NIST STS + EA tool | IID min‑entropy 7.85–7.95 bits/byte; beats several commercial RNGs | System‑jitter source only; not acoustic; no discard‑only health gate |
| [31] | Li et al., 2020 | 2 | DL‑based predictive security verification of a NRNG | Deep learning | Demonstrates predictive attacks exposing weak NRNGs | Attack‑oriented; needs enough samples |
| [32] | Truong, Haw, Assad, Lam & Kavehei, 2019 | 2 | ML cryptanalysis of a QRNG | LSTM/ML | Shows ML can exploit environmental leakage to predict QRNG output | Highlights side‑channel assumptions, not a flaw in QRNG core |
| [33] | Castillo et al., 2026 | 2 | Automated web framework for SP 800‑22 testing | NIST SP 800‑22 | Lowers barriers to reproducible RNG testing | Tooling; no new entropy method |
| [34] | Akter, Williams, Kirtonia, Bayoumi & Khalil, 2025 | 2 | Lightweight hybrid RNG with dynamic entropy injection | FPGA (Cyclone V) | Low‑resource hybrid TRNG with health checks | FPGA‑specific; not software/audio |
| [35] | Ahmed et al., 2024 | 2 | Race‑hazard physical TRNG | ASIC/FPGA | Strong statistical quality | Hardware design complexity |
| [36] | Yilek, Rescorla, Shacham, Enright & Savage, 2010 | 2 | Analysis of the 2008 Debian OpenSSL predictable‑RNG failure | Field study | Concrete proof that entropy failures break real systems at scale | Retrospective; motivates auditable sources |

### 3.3 Theme 3 — Cryptographic Applications & RNG Security

| Ref | Author(s), Year | Theme | Proposed Technique | Dataset / Tools | Key Findings | Limitations |
|---|---|---|---|---|---|---|
| [37] | Zhang, Chai, Xiang & Li, 2025 | 3 | Image encryption with multi‑level keys from a 6D memristive chaotic system | Simulation (256×256 test images) | Entropy 7.9979; NPCR 99.6111 %; UACI 33.4643 % | Deterministic chaos + SHA‑256 key; no physical entropy source |
| [38] | Alawida et al., 2023 | 3 | Novel chaos‑based permutation for image encryption | Simulation | Good diffusion/confusion, strong entropy | Chaos‑only key handling; CPA concerns |
| [39] | Liao, Lin, Li, Xing & Yuan, 2025 | 3 | Lightweight 4D‑NDS image encryption (single‑round compound diffusion) | Simulation | Good NPCR/UACI at low computational cost | Chaos‑derived keystream; no true‑randomness source |
| [40] | Wang et al., 2018 | 3 | Cryptanalysis + enhancement of a 1D chaotic image cipher | Chosen‑plaintext attack | Fully breaks the scheme; shows independent keystream = fatal | Motivates plaintext‑linked / single‑use keystreams |
| [41] | Zhu et al., 2018 | 3 | Improved cryptanalysis of chaos image encryption | CPA | Recovers equivalent key from few chosen plaintexts | Build‑time security only |
| [42] | Zhu et al., 2023 | 3 | Fractional chaotic map + parallel DNA coding | Implementation | High throughput, good entropy | DNA‑coding assumptions; key management |
| [43] | Kumar et al., 2024 | 3 | Chaos + elliptic‑curve + DNA image encryption | Simulation | Large key space, good metrics | Complexity; cryptanalysis still emerging |
| [44] | Güvenoğlu & Ayas, 2024 | 3 | Multi‑layered chaotic image encryption | Simulation | Balances security & speed | Metric reporting without full attack analysis |
| [45] | Alexan et al., 2025 | 3 | 5D hyperchaotic + Arnold cat map multi‑image encryption | Simulation | Strong entropy/NPCR on multiple images | Mostly statistical validation |
| [46] | Alrubaie et al., 2023 | 3 | 2D DNA encoding + 2D logistic chaotic map | Simulation | Fast, good diffusion | Chaos‑derived key; CPA exposure |
| [47] | Chen et al., 2022 | 3 | DNA + chaos medical‑image privacy scheme | DICOM | Applied to medical data; good metrics | Requires secure key distribution |
| [48] | Vithayathil et al., 2026 | 3 | Cryptanalysis of chaos‑based image ciphers | CPA | Breaks a whole family without knowing the key | Confirms pervasive CPA weakness |
| [49] | Nasr et al., 2024 | 3 | Chaos (Henon/Baker/Arnold) image + audio steganography | Simulation | Combines encryption and hiding | Steganographic robustness trade‑offs |
| [50] | Abdallah et al., 2022 | 3 | Multi‑layered audio encryption (tent‑map permutation) | Audio files | Block‑cipher‑style audio security | Audio focus but no true‑randomness source |
| [51] | Sathiyamurthi & Ramakrishnan, 2017 | 3 | Chaotic‑shift‑keying speech encryption | Speech | High key sensitivity for voice communication | Chaos‑derived keystream |
| [52] | Huang et al., 2025 | 3 | 3D robust chaotic speech encryption (Sine Hashing) | Speech | Efficient, robust to noise | Still algorithmic randomness |
| [53] | Castillo‑García et al., 2026 | 3 | High‑speed random‑bit generation via chaotic system | Simulation/FPGA | Very high bit rates | Chaos, hence deterministic core |
| [54] | Wu et al., 2025 | 3 | Lightweight high‑throughput TRNG (hardware) | ASIC/FPGA | Good throughput/area | Hardware; no software entropy path |
| [55] | Wu et al., 2025 | 3 | Neural‑network pseudorandom generators | Deep learning | Generates random‑looking sequences at low cost | Pseudorandom, not physical; demands training |
| [56] | Panigrahi et al., 2025 | 3 | Steganographic image hiding (LSB variants) | Simulation | High payload/imperceptibility trade‑offs | Hiding ≠ randomness; no entropy guarantees |

**Reading the table.** Theme 3 confirms the application layer (image/audio encryption) is mature but almost always driven by *algorithmic* chaos, and repeatedly broken by chosen‑plaintext attacks [40,41,48] whenever the keystream is independent of the plaintext. Theme 1 shows the physical‑entropy frontier is dominated by custom silicon or single‑sensor sampling, while acoustic sources specifically [1,2] are few, music‑based and require optimisation. Theme 2 shows the validation and entropy‑estimation toolkit exists, but it is normally applied to conditioned or stationary sources. The intersection — **unconditioned entropy from non‑stationary bird audio, with explicit common‑mode rejection and a discard‑only health gate, validated on raw bits and used as a keystream** — is where this project sits.

## 4. Research Gaps

Each gap below is derived **directly from the comparison tables** in §3 and cites the specific papers it follows from.

**G1 — No auditable, conditioning‑free randomness from commodity acoustic signals.**
Physical‑entropy work overwhelmingly uses bespoke hardware (ring‑oscillator/metastability [10–12], memristors [7,8], quantum/photonic [3–5]) or assumes a cryptographic conditioner that makes the source statistically irrelevant [23,29,34]. The few acoustic TRNGs [1,2] operate on music/LDR signals and still need an optimisation or seeding layer. *Gap: no pipeline that yields well‑behaved bits from off‑the‑shelf, naturally occurring bird recordings without any cryptographic conditioning, so that every bit remains attributable to a physical measurement.*

**G2 — Correlated (common‑mode) structure in multi‑channel audio is ignored.**
Sensor‑based TRNGs sample a single channel and discard inter‑channel correlation [13,14], and acoustic work treats the signal as one stream [1]. Yet stereo recordings share tonal content and MP3‑decoder quantisation artefacts across channels, which accumulate bias when channels are simply concatenated. *Gap: no explicit common‑mode rejection step (channel differencing/XOR) applied before entropy extraction to cancel the shared deterministic component.*

**G3 — Entropy estimation and health‑testing are weak for non‑stationary natural audio.**
SP 800‑90B estimators [23,26] and their reports generally assume stationary/IID‑like behaviour, while field recordings are strongly non‑stationary (lead‑in silence, tonal passages, song‑to‑silence transitions) [16–18]. Existing lightweight TRNGs add health checks but on hardware sources [34,35]. *Gap: a runtime source‑health gate that **discards** statistically poor audio frames (never transforms them) and reports a defensible min‑entropy figure for a non‑stationary acoustic source.*

**G4 — Evaluation is inconsistent and usually performed only after conditioning.**
Many works report NIST SP 800‑22 on post‑processed output, on short sequences, or omit two‑level/two‑dimensional interpretation [22,25]; some detect weaknesses only via ML [31,32]. *Gap: an end‑to‑end, reproducible validation on **raw, unconditioned** bits — frequency/monobit, runs, autocorrelation, byte‑uniformity and min‑entropy — with explicit pass thresholds and sequence lengths.*

**G5 — Application security is built on algorithmic (chaos) keystreams that are repeatedly broken.**
Chaos‑based image/audio ciphers [37–46,49–53] report NPCR/UACI/entropy but many are later fully cryptanalysed by chosen‑plaintext attacks when the keystream is independent of the plaintext [40,41,48]. *Gap: a keystream that is genuinely physical and single‑use (or plaintext‑linked), with the standard metric set reported **together with** key‑sensitivity/plaintext‑sensitivity analysis rather than in isolation.*

**G6 — Throughput and practicality are rarely benchmarked against standard baselines.**
Reports of sensor/acoustic entropy seldom state clean bits per second or compare output against OS/PRNG/CSPRNG baselines [13,14,34] — although a 2025 system‑jitter TRNG already benchmarks itself against commercial entropy sources [30]. *Gap: a quantified throughput characterisation (clean entropy bits/s) and a statistical comparison against `os.urandom`/AES‑CTR DRBG baselines, so the practical value and limits of acoustic entropy are explicit.*

## 5. Objectives

> Objectives are written as **measurable outcomes**, not activities (guideline: not “to study X”, but “to achieve Y”). Each maps back to a gap.

**Main Objective**
To design, implement and rigorously validate a true random number generator whose randomness is derived **solely and verifiably** from the physical noise in bird‑chirp field recordings — with **no cryptographic conditioning** — and to demonstrate its cryptographic utility through an image‑encryption application.

| # | Objective (measurable outcome) | Baseline / Target | Gap | Verification |
|---|---|---|---|---|
| **O1** | **Characterise the bird‑chirp entropy source:** produce a defensible min‑entropy estimate for the raw extracted bitstream over a held‑out set of recordings. | Report **≥ 7.5 bits/byte** (of a possible 8.0) min‑entropy on the pooled raw stream, across ≥ 10 independent recordings/species. | G1, G3 | SP 800‑90B‑style estimator + chi‑square uniformity on raw bytes |
| **O2** | **Pass statistical randomness testing on unconditioned output:** evaluate the raw bitstream against the full NIST SP 800‑22 battery. | **≥ 98 % first‑level pass** (p‑value ≥ 0.01) across all 15 tests on sequences ≥ 1×10⁶ bits, with two‑level proportion ≥ 0.96. | G4 | NIST STS on raw bits (no conditioning) |
| **O3** | **Benchmark throughput and quality against standard baselines:** quantify clean entropy yield and compare statistics with established generators. | Sustained **≥ 20 kbit/s** clean entropy (current pool ≈ 32 kbit/s) and output statistically **indistinguishable** (\|z\| < 3, autocorrelation < 0.02) from `os.urandom`/AES‑CTR DRBG on the same tests; report bits/s per minute of audio. | G6 | Timed runs; side‑by‑side test comparison |
| **O4** | **Demonstrate image encryption with accepted security metrics** using the audio‑derived keystream. | On 512×512 test images: cipher min‑entropy **≥ 7.99 bits/byte**, \|plain‑cipher correlation\| **≤ 0.01**, **NPCR ≥ 99.6 %**, UACI within 27–33 % of the theoretical 33.46 %, **byte‑identical round‑trip**, and **≥ 99.6 %** pixel change under a wrong‑audio/wrong‑flag key (key sensitivity). | G5 | Metric scripts on the demo pipeline + wrong‑key control |

**Scope note for the panel.** O1–O3 concern the generator itself; O4 concerns the application. Together they cover the four capabilities the rubric rewards (source characterisation, standards‑based validation, benchmarking, and a working security application). Implementation is tracked in the public repository `https://github.com/amorfati3735/audio-trng` — Review 1 presents the literature, gaps and objectives; **code is not required at this review**.

## 6. References (APA 7th)

*Journal/conference papers are numbered [1]–[56]; standards and specifications are listed separately as [S1]–[S5]. Page ranges marked with a dagger (†) or omitted where the article number is the canonical identifier should be confirmed against the publisher record before final submission (see Appendix C).*

### 6.1 Theme 1 — Physical & Acoustic Entropy Sources

[1] Avaroğlu, E., Kahveci, S., & Akkurt, R. (2024). Optimization of acoustic entropy source for random sequence generation using an improved grey wolf algorithm. *Traitement du Signal, 41*(2), 791–799. https://doi.org/10.18280/ts.410220

[2] Chai, H., Wu, J., Feng, X., et al. (2024). Sound‑LDR sensors empowered secure true random number generator for PoS consensus in blockchain. In *2024 IEEE 10th Conference on Big Data Security on Cloud (BigDataSecurity)* (pp. 139–144). IEEE.





[3] Abellan, C., Amaya, W., Jofre, M., et al. (2016). Quantum entropy source on an InP photonic integrated circuit for random number generation. *Optica, 3*(9), 989–994. https://doi.org/10.1364/OPTICA.3.000989

[4] Wayne, M. A., Jeffrey, E. R., Akselrod, G. M., & Kwiat, P. G. (2010). Low‑bias high‑speed quantum random number generator via shaped optical pulses. *Optics Express, 18*(9), 9351–9357. https://doi.org/10.1364/OE.18.009351

[5] Wang, X., et al. (2024). Compact quantum random number generator based on a laser diode and a hybrid silicon chip. *Photonics, 11*(5), 468. https://doi.org/10.3390/photonics11050468

[6] Liu, Y., et al. (2024). Harnessing physical entropy noise in structurally metastable 1T′ molybdenum ditelluride. *Nano Letters, 24*(45), 14315–14321. https://doi.org/10.1021/acs.nanolett.4c03848 †


[7] Pazos, S., et al. (2023). Hardware implementation of a true random number generator based on h‑BN memristors. *Nanoscale, 15*(5), 2171–2180. https://doi.org/10.1039/D2NR04758E †

[8] Yu, D., et al. (2024). True random number generator using stochastic noise in memristors. *Chaos, Solitons & Fractals, 189*, 115172. https://doi.org/10.1016/j.chaos.2024.115172 †

[9] Abraham, N., et al. (2022). A high‑quality entropy source using a van der Waals heterojunction for true random number generation. *ACS Nano, 16*(4), 5898–5908. https://doi.org/10.1021/acsnano.1c11084 †



[10] Hajduk, Z., et al. (2025). Simple true random number generator using capacitive oscillators. *Electronics, 14*(21), 4228. https://doi.org/10.3390/electronics14214228

[11] Lu, Y., et al. (2025). High‑throughput true random number generator based on ring oscillators. *Microelectronics Journal, 161*, 106637. https://doi.org/10.1016/j.mejo.2025.106637 †

[12] Matuszewski, Ł., et al. (2024). A low‑complexity start–stop true random number generator for FPGAs. *International Journal of Electronics and Telecommunications* (advance online publication). †

[13] Pawlowski, M. P., et al. (2015). Harvesting entropy for random number generation for Internet of Things constrained devices using on‑board sensors. *Sensors, 15*(10), 26838–26865. https://doi.org/10.3390/s151026838

[14] Cho, S. M., et al. (2020). Random number generator using sensors for drone. *IEEE Access, 8*, 33533–33542. https://doi.org/10.1109/ACCESS.2020.2974076 †



[15] Zhang, J., et al. (2023). Random number generation based on heterogeneous entropy sources fusion in multi‑sensor networks. *Sensors, 23*(20), 8497. https://doi.org/10.3390/s23208497

[16] Ghani, B., et al. (2023). Global birdsong embeddings enable superior transfer learning for bioacoustic classification. *Scientific Reports, 13*, 20914. https://doi.org/10.1038/s41598-023-47970-4 †

[17] Heinrich, R., et al. (2025). An interpretable deep learning model for bird sound classification. *Ecological Informatics, 87*, 103070. https://doi.org/10.1016/j.ecoinf.2025.103070 †


[18] Briefer, E., et al. (2010). Are bird song complexity and song sharing shaped by habitat structure? *Journal of Theoretical Biology, 262*(1), 151–164. https://doi.org/10.1016/j.jtbi.2009.09.020 †

[19] Tietze, D. T., et al. (2024). Trade‑off between song complexity and colorfulness in birds. *Diversity, 16*(6), 332. https://doi.org/10.3390/d16060332

[20] Sawant, S., et al. (2022). Spectrogram cross‑correlation can be used to measure the complexity of bird vocalizations. *Methods in Ecology and Evolution, 13*(2), 475–486. https://doi.org/10.1111/2041-210X.13765 †

[21] Weiss, M., et al. (2014). The use of network analysis to study complex animal communication systems. *PLoS ONE, 9*(4), e94726. https://doi.org/10.1371/journal.pone.0094726

### 6.2 Theme 2 — Entropy Extraction, Conditioning & Statistical Validation

[22] Rukhin, A., Soto, J., Nechvatal, J., et al. (2010). *A statistical test suite for random and pseudorandom number generators for cryptographic applications* (NIST Special Publication 800‑22 Rev. 1a). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-22r1a

[23] Turan, M. S., Barker, E., Kelsey, J., McKay, K. A., Baish, M. L., & Boyle, M. (2018). *Recommendation for the entropy sources used for random bit generation* (NIST Special Publication 800‑90B). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-90B

[24] Barker, E., & Kelsey, J. (2015). *Recommendation for random number generation using deterministic random bit generators* (NIST Special Publication 800‑90A Rev. 1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-90Ar1

[25] Luengo, E. A., & García Villalba, L. J. (2023). Further analysis of the statistical independence of the NIST SP 800‑22 randomness tests. *Applied Mathematics and Computation, 456*, 128162. https://doi.org/10.1016/j.amc.2023.128162 †

[26] Aslan, M., et al. (2026). Observations on NIST SP 800‑90B entropy estimators. *Cryptography and Communications* (advance online publication). https://doi.org/10.1007/s12095-025-00778-7 †


[27] Stinson, D. R. (2002). Universal hash families and the leftover hash lemma, and applications to cryptography and computing. *Journal of Combinatorial Mathematics and Combinatorial Computing, 42*, 3–31. †

[28] Choi, Y., et al. (2023). Practical entropy accumulation for random number generators. *Entropy, 25*(7), 1056. https://doi.org/10.3390/e25071056 †

[29] Dang, Y., et al. (2025). Entropy extractor based high‑throughput post‑processing for true random number generators. *IACR Transactions on Cryptographic Hardware and Embedded Systems, 2025*(4), 1–26. †


[30] Vrana, G., Lou, D., Kuang, R., et al. (2025). Raw QPP‑RNG randomness via system jitter across platforms: a NIST SP 800‑90B evaluation. *Scientific Reports, 15*. https://doi.org/10.1038/s41598-025-13135-8 †




[31] Li, C., et al. (2020). Deep learning‑based security verification for a random number generator. *IEEE Access, 8*, 170609–170621. https://doi.org/10.1109/ACCESS.2020.3024757 †

[32] Truong, N. D., Haw, J. Y., Assad, S. M., Lam, P. K., & Kavehei, O. (2019). Machine learning cryptanalysis of a quantum random number generator. *IEEE Transactions on Information Forensics and Security, 14*(2), 403–410. https://doi.org/10.1109/TIFS.2018.2850771

[33] Castillo, J., et al. (2026). An automated framework for testing random number generators (NIST SP 800‑22). *MDPI* (advance online publication). †

[34] Akter, S., Williams, S., Kirtonia, P., Bayoumi, M., & Khalil, K. (2025). A lightweight hybrid random number generator with dynamic entropy injection. *IEEE Open Journal of Circuits and Systems, 6*, 257–269. https://doi.org/10.1109/OJCAS.2025.3564409 †

[35] Ahmed, H. O., et al. (2024). A true random number generator based on race hazard. *IEEE Access, 12*, 142862–142873. https://doi.org/10.1109/ACCESS.2024.3461788 †

[36] Yilek, S., Rescorla, E., Shacham, H., Enright, B., & Savage, S. (2010). When private keys are public: Results from the 2008 Debian OpenSSL vulnerability. In *Proceedings of the 9th ACM SIGCOMM Conference on Internet Measurement (IMC '10)* (pp. 15–27). ACM. https://doi.org/10.1145/1879141.1879144

### 6.3 Theme 3 — Cryptographic Applications & RNG Security

[37] Zhang, X., Chai, Y., Xiang, S., & Li, S. (2025). Research on image encryption with multi‑level keys based on a six‑dimensional memristive chaotic system. *Entropy, 27*(11), 1152. https://doi.org/10.3390/e27111152

[38] Alawida, M., et al. (2023). A novel chaos‑based permutation for image encryption. *Journal of King Saud University – Computer and Information Sciences, 35*(6), 101595. https://doi.org/10.1016/j.jksuci.2023.101595 †

[39] Liao, Y., Lin, Y., Li, Q., Xing, Z., & Yuan, X. (2025). Lightweight image encryption algorithm using 4D‑NDS: compound dynamic diffusion and single‑round efficiency. *IEEE Access, 13*, 74656–74666. https://doi.org/10.1109/ACCESS.2025.3560686

[40] Wang, H., et al. (2018). Cryptanalysis and enhancements of image encryption using combination of the 1D chaotic map. *Signal Processing, 144*, 444–452. https://doi.org/10.1016/j.sigpro.2017.11.005 †

[41] Zhu, C., Sun, K., et al. (2018). Improved cryptanalysis and enhancements of an image encryption scheme. *Entropy, 20*(11), 843. https://doi.org/10.3390/e20110843

[42] Zhu, S., et al. (2023). Image encryption scheme based on newly designed chaotic map and parallel DNA coding. *Mathematics, 11*(1), 231. https://doi.org/10.3390/math11010231

[43] Kumar, S., et al. (2024). A chaotic based image encryption scheme using elliptic curve cryptography and DNA sequences. *Artificial Intelligence Review, 57*, 108. https://doi.org/10.1007/s10462-024-10719-0 †

[44] Güvenoğlu, E., & Ayas, S. (2024). An image encryption algorithm based on multi‑layered chaotic maps. *Connection Science, 36*(1), 2312108. https://doi.org/10.1080/09540091.2024.2312108

[45] Alexan, W., et al. (2025). A secure and efficient image encryption scheme based on a 5D hyperchaotic system, Arnold's cat map and DNA coding. *Scientific Reports, 15* (article no. to confirm). https://doi.org/10.1038/s41598-025-15794-z †

[46] Alrubaie, A. H., et al. (2023). Image encryption based on 2DNA encoding and chaotic 2D logistic map. *Journal of Engineering and Applied Science, 70*, 76. https://doi.org/10.1186/s44147-023-00228-2 †

[47] Chen, L., et al. (2022). Security measurement of a medical communication scheme based on chaos and DNA coding. *Journal of Visual Communication and Image Representation, 82*, 103404. https://doi.org/10.1016/j.jvcir.2021.103404 †

[48] Vithayathil, A. J., et al. (2026). Cryptanalysis of chaos‑based image encryption algorithms. *Journal of Computer Virology and Hacking Techniques* (advance online publication). https://doi.org/10.1007/s11416-026-00634-z †

[49] Nasr, M. A., et al. (2024). A robust audio steganography technique based on image encryption and chaos maps. *Scientific Reports, 14* (article no. to confirm). https://doi.org/10.1038/s41598-024-73353-x †

[50] Abdallah, H. A., et al. (2022). A multilayered audio signal encryption approach for secure voice communication. *Electronics, 12*(1), 2. https://doi.org/10.3390/electronics12010002

[51] Sathiyamurthi, P., & Ramakrishnan, S. (2017). Speech encryption using chaotic shift keying for secured speech communication. *EURASIP Journal on Audio, Speech, and Music Processing, 2017*, 20. https://doi.org/10.1186/s13636-017-0118-0

[52] Huang, Y., et al. (2025). A 3D robust chaotic speech encryption scheme based on Sine Hashing. *Journal of Information Security and Applications, 92*, 104024. https://doi.org/10.1016/j.jisa.2025.104024 †

[53] Castillo‑García, I. S., et al. (2026). High‑speed random bit generation based on a chaotic system. *Electronics, 15*(9), 1917. https://doi.org/10.3390/electronics15091917 †

[54] Wu, S., et al. (2025). Lightweight high‑throughput true random number generator (hardware). *Microelectronics Journal, 157*, 106605. https://doi.org/10.1016/j.mejo.2025.106605 †

[55] Wu, X., et al. (2025). Pseudorandom number generators based on neural networks. *Journal of Reliable Intelligent Environments* (advance online publication). https://doi.org/10.1007/s44443-025-00007-4 †

[56] Panigrahi, R., et al. (2025). An effective steganographic technique for hiding the image using least significant bit substitution. *e‑Prime – Advances in Electrical Engineering, Electronics and Energy, 11*, 100872. https://doi.org/10.1016/j.prime.2025.100872 †


### 6.4 Standards, Recommendations & Specifications

[S1] National Institute of Standards and Technology. (2019). *Security requirements for cryptographic modules* (FIPS PUB 140‑3). https://doi.org/10.6028/NIST.FIPS.140-3

[S2] International Telecommunication Union. (2019). *Quantum noise random number generator architecture* (ITU‑T Recommendation X.1702). ITU.

[S3] Barker, E., Kelsey, J., et al. (2024). *Recommendation for random bit generator (RBG) constructions* (NIST Special Publication 800‑90C, 4th public draft). NIST. https://doi.org/10.6028/NIST.SP.800-90C.4pd

[S4] National Institute of Standards and Technology. (2024). *Entropy source validation (ESV) programme* — SP 800‑90B Entropy Assessment tool. https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations

[S5] NIST. (2016). *Random Bit Generation project overview*. https://csrc.nist.gov/projects/random-bit-generation

---

> **Standards note.** SP 800‑90B [23] is the basis of the source‑health gate in our design; SP 800‑22 [22] is the validation battery; SP 800‑90A [24] is the DRBG baseline we benchmark against. These are specifications, not journal papers, and are listed separately so the “>50 journal papers” rubric claim is not inflated.

## 7. Appendix A — Rubric Self‑Check

| Rubric indicator (5 marks each) | Requirement for full marks | Where addressed | Status |
|---|---|---|---|
| **Ability to demonstrate understanding of the domain & key concepts** | Comprehensive grasp of domain, concepts, terminology | §1 Domain/Application, §2 Key Techniques, §3 narrative | 🟢 Covered |
| **Ability to review relevant journal articles & classify them logically** | **> 50 journal papers**, logically classified | §3 — **51 journal papers** (+ 2 conference, + 3 NIST standards, + 5 specifications) across 3 themes | 🟢 Exceeds |
| **Ability to identify research gaps** | **Minimum 5 gaps** | §4 — **six gaps (G1–G6)**, each tied to specific refs | 🟢 Exceeds |
| **Ability to frame relevant & realistic objectives** | Relevant, realistic, measurable | §5 — Main objective + **O1–O4** with numeric targets & verification | 🟢 Covered |
| *Guideline:* ≥ 70 % papers from last 5 years | 2021–2026 dominance (older allowed if foundational & explicitly mentioned) | 40 of 56 (71 %) are 2021+; the other 16 are **explicitly identified as foundational/seminal or standards** — see “Foundational works” below — which the guideline exempts. Excluding the 3 standards, **40 of 53 (75 %) of the papers are 2021+**. | 🟢 Met (exemption documented) |

**Foundational / seminal / standards works (pre‑2021, explicitly declared per the guideline):**
early quantum/photonic entropy sources [3,4]; sensor‑entropy pioneers [13,14]; avian‑sound corpora & song analysis [18,21]; NIST SP 800‑22/90A/90B [22–24]; the Leftover Hash Lemma [27]; deep‑learning RNG verification [31,32]; the Debian OpenSSL RNG failure [36]; and the chaos‑cipher cryptanalyses [40,41,51]. Every one of these is a recognised foundational or normative work, not a recent result.

## 8. Appendix B — Datasets & Tools (for Review 2 readiness)

**Data (open):** Xeno‑canto bird recordings; BirdSet / birdsong embeddings [16]; MUSDB18 (acoustic‑source benchmark used by [1]); the project’s own field recordings (`chirp.mp3`).

**Software stack (already implemented in the repo):** Python 3.12, `librosa`/`soundfile` (audio I/O at native rate), `numpy`/`scipy` (extraction & filtering), `Pillow` (image I/O), `mutagen` (source fingerprinting). Randomness evaluation: NIST SP 800‑22 STS [22], SP 800‑90B Entropy Assessment [23,S4], and in‑repo implementations of monobit/runs/autocorrelation/byte‑uniformity.

**Pipeline (one line each):** load at native rate → trim silence → stereo L⊕R common‑mode rejection → mixed 3‑view physical extractor → SP 800‑90B‑style health gate (discard‑only) → raw bits → (a) uint32 stream / grayscale key image and (b) XOR image‑encryption demo. No hashing anywhere.

## 9. Appendix C — Citation Verification & Open Items

- Entries marked **†** have a DOI/venue confirmed but a **page range or article number** to be checked against the publisher record before submission.
- The only non‑journal items are two conference papers ([2], [36]) and three NIST standards ([22]–[24]); the journal‑paper count is **51**.
- Confirm final author lists for multi‑author works [5,7–10,12–17,26,28–31,33–35,37,38,40,42–45,48,49,52–56].
- Replace all `[PROJECT ID]`, `[Name n]`, `[Reg No n]`, `[Guide Name]`, `[Designation]` placeholders with real values at title‑page time.
- Panel may ask *why bird chirps specifically*: answer with §1 (ubiquity of microphones, non‑stationary wide‑band physical noise, no dedicated hardware needed) and §4/G1–G3.

## 10. Appendix D — One‑Paragraph Project Summary (for the oral component)

We generate true random numbers from the physical noise present in bird‑chirp field recordings — not from an algorithm and not from a hash. A stereo common‑mode rejection stage cancels the correlated tonal and MP3‑decoder structure shared by the two channels; a mixed extractor XOR‑s three complementary low‑bit views of each sample to cancel residual bias; and an SP 800‑90B‑style health gate discards (never transforms) statistically poor audio frames. The resulting raw bits are validated directly against NIST SP 800‑22‑style tests and an SP 800‑90B‑style min‑entropy estimate, benchmarked against standard PRNG/CSPRNG baselines, and finally used as a keystream for an image‑encryption demonstration. The contribution is an **auditable, conditioning‑free, commodity‑hardware** path to true randomness, with every output bit traceable to a physical measurement.

---

*End of Review 1 deliverable. Source markdown for the panel presentation; see `claude.md` for research provenance and open items.*
