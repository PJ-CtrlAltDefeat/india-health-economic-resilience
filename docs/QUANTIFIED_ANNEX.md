# Quantified Annex: The Health–Growth Dilemma

Companion to the policy paper and deck in this folder. It does three things:

1. **Fact-checks** the headline numbers in the original documents against published sources.
2. **Costs** the paper's three funded levers (digital health, Pandemic Preparedness Fund, UHC expansion) from FY2027 to FY2047.
3. **Stress-tests** five of the paper's claims with explicit assumptions and sensitivity ranges.

All figures are produced by [`src/model.py`](../src/model.py). Every input is in [`data/assumptions.csv`](../data/assumptions.csv) with a source and a confidence tag:

| Tag | Meaning |
|---|---|
| **V** | Verified against a published source |
| **P** | Taken from the paper itself (a design choice or claim) |
| **A** | Analyst assumption, illustrative. Replace with better data |

Money is in ₹ crore, nominal. 1 lakh crore = 100,000 crore. FY2027 means April 2026 – March 2027.

---

## 1. Fact-check of the original numbers

Full table: [`data/fact_check.csv`](../data/fact_check.csv). The ones that matter most:

| Paper says | Sources show | Status |
|---|---|---|
| 70% of health costs paid out of pocket | **39.4%** of total health expenditure in 2021-22 (62.6% in 2014-15) | Outdated |
| COVID lockdowns shrank GDP 9% | **−7.3%** (provisional), **−6.6%** (Jan 2022 revised) for FY2020-21 | Incorrect for COVID. Fine as a 2030 *scenario* |
| 6 crore pushed into poverty (NITI Aayog) | **5.5 crore in 2017**, from a PHFI study | Misattributed |
| Ayushman Bharat "covered" 50 crore | ~55 crore *eligible*; 35.4 crore cards issued | Imprecise |
| Insurance + prevention cuts costs "up to 40%" | PM-JAY beneficiaries saw **−21%** OOP | Unsupported at 40% |
| 1 government doctor per 11,000 | Not verified; official ratios are 1:834 (incl. AYUSH) / ~1:1,194 (allopathic, 2022) | Unverified |

**Recommendation before publishing the paper itself:** correct the first five rows. The model below uses the corrected values.

---

## 2. What the package costs

Scope: the three levers the paper puts a number or a coverage target on.

| Lever | Paper's figure | How it is scheduled in the model |
|---|---|---|
| Digital health | ₹50,000 cr over 5 years | ₹10,000 cr/yr, FY2027–31 |
| Pandemic Preparedness Fund | ₹1 lakh cr | ₹10,000 cr/yr, FY2027–36 (schedule is my assumption) |
| UHC expansion | 70% of informal workers by 2027, 100% by 2047 | Baseline 48.1% (15.10 cr of 31.38 cr e-Shram registrants already PM-JAY-linked). Extra people × ₹500 premium (FY27), +5%/yr |

![Annual cost](../results/01_annual_cost.png)

| Result | Value |
|---|---|
| FY2027 cost | **₹21,716 cr = 0.056% of GDP** (this is the peak) |
| Cumulative FY2027–47 | **₹3.66 lakh cr** (digital 0.50, fund 1.00, UHC 2.16) |
| Range if premium is ₹300 / ₹1,000 per person | ₹2.80 / ₹5.83 lakh cr |
| Extra people covered | 6.9 crore by FY2028; 16.3 crore by FY2047 |

**Reading:** the funded commitments are small relative to the economy. If the paper's plan fails, money is unlikely to be the binding constraint. Execution is.

**Not costed** (no defensible data): recurrent running costs of the digital platform, the 50% domestic-procurement mandate, workforce expansion, climate-resilient facilities, mental-health integration, and any relief payments. So 0.056% of GDP is a floor, not the full bill.

---

## 3. Does it pay for itself? A break-even analysis

I do not know the true probability of a pandemic-scale shock, or how much preparedness reduces its damage. So instead of picking one answer, the model shows the **break-even**: how much GDP loss must preparedness avoid for benefits to equal costs?

Benefit = probability of shock per year × GDP loss avoided (pp) × GDP, discounted at 9% nominal. Costs cover digital health and the fund only (the pandemic-specific levers).

![Benefit-cost heatmap](../results/02_benefit_cost_heatmap.png)

| Annual shock probability | Break-even GDP loss avoided (digital + fund) | Break-even (whole package incl. UHC) |
|---|---|---|
| 0.5% | 2.39 pp | 4.04 pp |
| 1% | 1.20 pp | 2.02 pp |
| 2% | **0.60 pp** | **1.01 pp** |
| 3% | 0.40 pp | 0.67 pp |
| 5% | 0.24 pp | 0.40 pp |

At the base case (2% a year, 1.5 pp avoided out of a 9 pp shock) the benefit-cost ratio is **2.5** for the preparedness levers and **1.5** for the whole package, counting pandemic benefits only. UHC's non-pandemic benefits (lower OOP, fewer poverty spells) are excluded, so the package figure is conservative. The 2% base probability is a placeholder, and the heatmap shows what happens if it is wrong.

---

## 4. The fund is smaller than the problem it is meant to absorb

The paper pairs a ₹1 lakh cr fund with "UBI for informal workers" during crises. What does that relief cost?

![Relief vs fund](../results/03_relief_vs_fund.png)

- Support of ₹3,000/month for 3 months to all 31.38 crore e-Shram workers costs **₹2.82 lakh cr**.
- The fund covers **35%** of that, or about **1.06 months** of support.
- Even the most modest scenario (₹2,000 × 2 months) is ₹1.26 lakh cr, which is above the fund.

**Implication for the policy:** the fund should be framed as a first-loss reserve, paired with a contingent credit line or RBI liquidity window and targeted rather than universal transfers. The paper already mentions RBI instruments, so this connects two sections it currently treats separately.

---

## 5. What "up to 40% lower costs" would imply

Data: [`results/oop_sensitivity.csv`](../results/oop_sensitivity.csv).

OOP spending in FY2022 was 39.4% × ₹9.04 lakh cr = **₹3.56 lakh cr**.

| OOP reduction | Saving (FY22 prices) | OOP share of THE | If publicly financed: extra spend | Government health spend |
|---|---|---|---|---|
| 10% | ₹0.36 lakh cr | 35.5% | 0.15% GDP | 1.99% GDP |
| **21% (PM-JAY observed)** | ₹0.75 lakh cr | 31.1% | 0.32% GDP | 2.16% GDP |
| 40% (paper) | ₹1.43 lakh cr | 23.6% | 0.60% GDP | 2.44% GDP |

A 40% cut is not free. Unless households simply spend less, someone else pays, which raises government health spending from 1.84% to roughly 2.4% of GDP. The paper's fiscal-viability answer should say so. The 21% case is the evidence-based version.

---

## 6. Doctors: what 1.5 per 1,000 by 2047 requires

![Doctors](../results/04_doctor_path.png)

- 2022 baseline: 10.46 lakh available allopathic doctors (govt figure: 13.08 lakh registered × 80%).
- The government's 1:1,194 uses roughly a 124 crore population. On ~1.41 bn people the ratio is **0.74 per 1,000 (1:1,348)**.
- Target: 1.5 per 1,000 × ~1.63 bn people (2047) = 24.5 lakh doctors, i.e. **~14 lakh net additions, ~56,000 a year, 3.5% annual growth**.

**Reading:** a national average of 1.5 is a modest target, and the path crosses the WHO 1.0 norm around 2032. The real problem in the paper's own diagnosis is *distribution* (Bihar/UP vs Kerala). The target would be stronger set as a state-level floor.

---

## Limitations

- Population (1.41 bn in 2022, 1.63 bn in 2047), nominal GDP growth (10.5%), premium (₹500), discount rate (9%), shock probability (2%) and loss avoided (1.5 pp) are my assumptions. They are flagged **A** in the register and swept where they matter.
- GDP is derived as total health expenditure ÷ 3.83% = ₹236 lakh cr for FY2022, then grown at 10.5%. I could not retrieve the FY2025 provisional estimate to cross-check.
- "Linked to PM-JAY" among e-Shram registrants is not the same as holding an active, usable card.
- The informal-worker pool is held flat at 31.38 crore. Real growth in registrations would raise UHC costs.
- This is an illustrative planning model, not a forecast and not an official costing.

---

## Sources

- National Health Accounts estimates 2020-21 and 2021-22: [Drishti IAS summary](https://www.drishtiias.com/daily-updates/daily-news-analysis/national-health-account-nha-estimates-2020-21-and-2021-22/print_manually) (original: [PIB, Oct 2024](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/oct/doc2024104408201.pdf))
- FY2020-21 GDP: [MoSPI press note, 31 May 2021](https://mospi.gov.in/sites/default/files/press_release/Press%20Note_31-05-2021.pdf); [Business Today on the Jan 2022 revision](https://www.businesstoday.in/amp/latest/economy/story/indias-gdp-contracts-by-66-in-fy21-govt-320962-2022-01-31)
- Doctor-population ratio: [ThePrint, Rajya Sabha reply (Jul 2022)](https://theprint.in/health/indias-doctor-patient-ratio-better-than-who-norm-of-11000-government-tells-rajya-sabha/1273080)
- PM-JAY: [Drishti IAS, Oct 2025](https://www.drishtiias.com/daily-updates/daily-news-analysis/ayushman-bharat-and-universal-health-coverage/print_manually)
- e-Shram: [Ministry of Labour release, 1 Dec 2025](https://labour.gov.in/sites/default/files/pib2196927.pdf)
- OOP and poverty: [The Quint on the PHFI study](https://www.thequint.com/fit/health-expenses-pushed-indians-into-poverty)
