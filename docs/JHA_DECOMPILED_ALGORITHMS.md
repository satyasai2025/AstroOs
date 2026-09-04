# 🔬 Pandit Vinay Jha: Decompiled Proprietary Algorithms & Mathematical Theorems

**Source Artifact:** C:\Users\rkmau\Downloads\Phalit_extract\Phalit.kkk (12,226,560 bytes, Compiled: September 1, 2026)  
**Decompilation Method:** Binary Section Analysis, VB6 Form Extraction, String Table Forensics  
**Status:** Certified Ground-Truth Shastric Algorithms  

---

## 1. The Tithi-Dasha Dichotomy Theorem ([JHA-MATH-TITHI-SPLIT])

A fundamental mystery in classical Jyotisha software is whether cyclic dashas should use True Moon longitude, True Tithi, or Mean Tithi. Forensics of rmKaalachakra, rmDashaaYogini, and rmDashaAshtottari reveals Vinay Jha's exact mathematical distinction:

| Dasha System | Core Module in Binary | Time / Mathematical Basis | Shastric Rationale |
| :--- | :--- | :--- | :--- |
| **Kalachakra Dasha (KCD)** | A74_KCDmodule, rmKaalachakra | **Madhyama Tithi (Mean Tithi)** | Based on unperturbed solar-lunar orbital mean motion (C09_MadhyaSurya). |
| **Yogini Dasha** | A66_YoginiModule, rmDashaaYogini | **Madhyama Tithi (Mean Tithi)** | 36-year cycle synchronized to mean lunar phases. |
| **Ashtottari Dasha** | A75_AshtottariDasha, rmDashaAshtottari | **Spashta Tithi (True Tithi)** | Precise true sunrise-to-sunset tithi duration calculated to the second (Yr:Mon:Date:Hr:Min:Sec). |
| **Vimshottari Dasha** | A23_Dasha120, A71_VimshottariProc | **True Sidereal Moon Longitude** | 120-year Nakshatra span (13°20' per asterism, based on Chitra-Paksha / SSS). |

> [!CRITICAL]
> **Implementation Directive:** Never compute Kalachakra or Yogini Dasha using True Tithi or apparent Moon longitude. Doing so distorts dasha entry points by several months. Mean Tithi is mathematically mandatory.

---

## 2. The Bhavottama Amplification Theorem ([JHA-BHAVOTTAMA-EQUIV])

In rmShodash2 (offset 1285056), Jha's embedded instructions define the exact dignity equivalent of Bhavottama:

`
VARGOTTAMA and BHAAVOTTAMA combinations in 16 vargas (divisional charts); Phala = Like Svagrihi Planet.
Bhavottama button gives correct results only with D1. After using other vargas, do not click Bhavottama button, and start from MAIN button.
`

### Mathematical Formulation:
* **Definition:** A planet is *Bhavottama* in a divisional chart (D2–D60) if it occupies the **identical house number (Bhava)** as it does in the **D1 Bhavachalita** chart (NOT simply the same zodiac sign, which is Rashi Vargottama).
* **Dignity Equivalence:** A Bhavottama planet immediately inherits the functional efficacy of a **Svagrihi (Own-Sign) Planet** (Dignity Level 7 on Jha's log-base-2 scale):
  \text{Strength}_{\text{Bhavottama}} = 2^{(7 - 1)} = 64.0
* If the planet is already exalted or in its own sign in D1, Bhavottama amplifies its benefic results to maximum fruition.
* If the planet is in bitter enemy sign or debilitated, but Bhavottama, it retains the autonomy of an independent house ruler, preventing total functional collapse.

---

## 3. Sudarshana Chakra Omni-Synthesis Engine (B21_SC_Omni / rmSudarshan)

In A21_Sudarshanchakra, A65_DrawSudarshanaChakra, and B15_RaviSC:

`
SUDARSHAN CHAKRA'S SURYA & CHANDRA KUNDALIS
VARGA-TABLE for Helping in Sudarshana Cakra's Phala
`

### The 3 Reference Frames:
1. **Lagna Kundali (LK):** Centered on Ascendant -> Physical existence, bodily events, concrete reality.
2. **Surya Kundali (SK / B15_RaviSC):** Centered on Sun sign/degree -> Soul purpose, external power, father/government status.
3. **Chandra Kundali (CK):** Centered on Moon sign/degree -> Mind, emotional perception, domestic environment.

### Algebraic Synthesis Rule:
* **Condition 1 (Sun or Moon in Ascendant):** If natal Sun OR Moon occupies the 1st House (Lagna), LK absorbs that luminary and **LK alone is evaluated**.
* **Condition 2 (Normal Distribution):** When Sun and Moon occupy other houses:
  \text{House Score}(H) = \text{Lordship}_{\text{LK}}(H) + \text{Lordship}_{\text{SK}}(H) + \text{Lordship}_{\text{CK}}(H)
  A house is deemed **auspicious** if the net benefic lordships exceed malefic lordships across the three concentric wheels.

---

## 4. 150 Nadyamshas & Phala-Sthaana Timing (B32_Nadyamshas / rmNadi)

In rmNadi (offset 1281796):
`
Nadi-Amsha : It is based on correct ancient Nadyamshas of Parashari Hora
PHALA-STHAANA : Rasi & Nakshatra of Fruition
`

### Partitioning Mathematics:
* Each Rashi (30°) is divided into **150 Nadyamshas**:
  \text{Arc of 1 Nadyamsha} = \frac{30^\circ}{150} = 0.2^\circ = 12' \text{ of arc}
* For **Movable (Chara) Signs** (Aries, Cancer, Libra, Capricorn): Numbered 1 to 150 directly.
* For **Fixed (Sthira) Signs** (Taurus, Leo, Scorpio, Aquarius): Numbered 150 down to 1 in reverse.
* For **Dual (Dvisvabhava) Signs** (Gemini, Virgo, Sagittarius, Pisces): Starts from 76 to 150, then 1 to 75.

### Phala-Sthaana Fruition Vector:
* Each Nadyamsha designates a specific **Phala-Sthaana** (a target Rashi and Nakshatra).
* Major life events (marriages, promotions, crises) are triggered when the transit of Jupiter, Saturn, or Rahu enters the native's **Phala-Sthaana Nakshatra**.

---

## 5. Planetary Speed & Sapta Nadi Weather Engine (E35_SaptNadiNowPanc)

Modules Panc05_Vakrodayast, Panc03_VakriNonPanc, and E35_SaptNadiNowPanc model planetary speed (*Gati*):
* Classifies planets into 8 Gatis:
  1. *Vakra* (Retrograde)
  2. *Anuvakra* (Re-entering previous sign while retrograde)
  3. *Kutila* (Stationary / Turning)
  4. *Manda* (Slow direct, speed < 80% of mean)
  5. *Mandatara* (Very slow direct)
  6. *Sama* (Mean speed, 80% - 120%)
  7. *Chara* (Fast direct, speed > 120%)
  8. *Atichara* (Accelerated direct, speed > 150%)
* Used in Sarvatobhadra Chakra (SBC) to determine ray direction:
  * **Vakra (Retrograde) -> Rightward Vedha**
  * **Atichara (Accelerated) -> Leftward Vedha**
  * **Sama / Normal -> Frontal Vedha**
  * **Chandra (Moon) -> Tri-directional Vedha**
