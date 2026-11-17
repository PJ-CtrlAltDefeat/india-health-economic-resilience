"""
Quantitative model for "Healthcare & Economy: The Health-Growth Dilemma"
(India National Health-Economic Resilience Policy, 2030 and beyond).

Run:  python src/model.py
Writes CSVs + a summary JSON to results/, charts (PNG) to results/, and the
assumption register to data/assumptions.csv.

Conventions
- Money is in Rs crore (1 lakh crore = 100,000 crore) and NOMINAL unless stated.
- Fiscal years are labelled by the year they end (FY2027 = Apr 2026 - Mar 2027).
- Every input lives in PARAMS with a source and a confidence tag. Nothing is
  hard-coded further down. Change a number there and everything re-runs.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------------------
# 1. PARAMETER REGISTER
#    confidence: V = verified against a published source this session
#                P = taken from the policy paper itself (design choice / claim)
#                A = analyst assumption, illustrative, replace with better data
# ---------------------------------------------------------------------------
P = {}


def param(key, value, unit, source, conf):
    P[key] = dict(value=value, unit=unit, source=source, confidence=conf)


# --- verified baselines ---
param("the_fy22", 904461, "Rs crore", "National Health Accounts 2021-22 (MoHFW, Oct 2024): total health expenditure", "V")
param("the_gdp_share_fy22", 0.0383, "share of GDP", "NHA 2021-22: THE = 3.83% of GDP", "V")
param("ghe_gdp_share_fy22", 0.0184, "share of GDP", "NHA 2021-22: government health expenditure = 1.84% of GDP", "V")
param("oop_share_fy22", 0.394, "share of THE", "NHA 2021-22: OOPE = 39.4% of THE (62.6% in 2014-15)", "V")
param("eshram_registered_cr", 31.38, "crore workers", "Ministry of Labour PIB release, 1 Dec 2025 (as of Nov 2025)", "V")
param("eshram_pmjay_linked_cr", 15.1006, "crore workers", "Same release: e-Shram registrants benefiting from PM-JAY (19 Nov 2025)", "V")
param("pmjay_oop_reduction", 0.21, "share", "NHA/PM-JAY summary: OOP expenses of beneficiaries fell 21% (beneficiary households, not national)", "V")
param("alloc_doctors_2022", 1046407, "doctors", "Govt reply to Rajya Sabha (Jul 2022): 13,08,009 registered allopathic doctors x 80% assumed available", "V")
param("covid_gdp_fy21_provisional", -0.073, "real GDP growth", "MoSPI provisional estimate, 31 May 2021", "V")
param("covid_gdp_fy21_revised", -0.066, "real GDP growth", "NSO first revised estimate, 31 Jan 2022", "V")
param("phfi_poverty_cr", 5.5, "crore people/yr", "PHFI study (Jun 2018): 55 million pushed into poverty by OOP health spending in 2017", "V")

# --- paper's own design choices ---
param("digital_total_cr", 50000, "Rs crore", "Paper s.4A / slide 7: Rs 50,000 crore digital health over 5 years", "P")
param("digital_years", 5, "years", "Slide 7: five years", "P")
param("fund_total_cr", 100000, "Rs crore", "Paper s.4C / slide 7: Rs 1 lakh crore Pandemic Preparedness Fund", "P")
param("fund_years", 10, "years", "Funding horizon for the pre-funded reserve (paper says 'pre-funded'; schedule is mine)", "A")
param("uhc_target_2028", 0.70, "share of informal workers", "Paper s.4B: 70% of informal workers covered by 2027", "P")
param("uhc_target_2047", 1.00, "share of informal workers", "Paper s.6/7: nationwide / 100% informal workers by 2047", "P")
param("doctor_target_2047", 1.5, "doctors per 1,000", "Paper s.6: 1.5 per 1,000 by 2047", "P")
param("shock_gdp_loss_pp", 9.0, "pp of GDP", "Paper scenario: 2030 pandemic shrinks GDP 9% (kept as the scenario shock; not a COVID fact)", "P")

# --- analyst assumptions (illustrative) ---
param("gdp_nominal_growth", 0.105, "per year", "Nominal GDP growth (6.5% real + ~4% deflator). Back-cast check: gives ~Rs 319 lakh cr in FY25", "A")
param("premium_per_person_fy27", 500, "Rs per person per year", "Insurance premium per additionally covered informal worker. Replace with state tender data", "A")
param("premium_inflation", 0.05, "per year", "Medical premium inflation", "A")
param("pop_2022_bn", 1.41, "billion", "Approx. India population 2022 (UN WPP medium variant; not re-verified here)", "A")
param("pop_2047_bn", 1.63, "billion", "Approx. India population 2047 (UN WPP medium variant; not re-verified here)", "A")
param("shock_prob", 0.02, "per year", "Annual probability of a COVID-scale shock (literature-informed placeholder; swept 0.5%-5%)", "A")
param("loss_avoided_pp", 1.5, "pp of GDP", "GDP loss avoided per shock thanks to preparedness (swept 0.5-3 pp)", "A")
param("discount_nominal", 0.09, "per year", "Nominal discount rate", "A")
param("relief_amount", 3000, "Rs per worker per month", "Illustrative relief transfer during a lockdown (swept 2,000-5,000)", "A")
param("relief_months", 3, "months", "Illustrative lockdown relief duration (swept 2-6)", "A")

V = {k: v["value"] for k, v in P.items()}
YEARS = np.arange(2027, 2048)  # FY2027..FY2047

# Colours: restrained, colour-blind-safe-ish, text stays in neutral ink.
C_BLUE, C_ORANGE, C_TEAL, C_GREY, INK = "#2F6DB5", "#D9822B", "#2A9D8F", "#8A8F98", "#222222"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#BBBBBB")
    ax.tick_params(colors=INK)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# 2. MACRO BASE: nominal GDP path (derived from verified NHA ratio)
# ---------------------------------------------------------------------------
gdp_fy22 = V["the_fy22"] / V["the_gdp_share_fy22"]  # Rs crore
gdp = pd.Series({int(y): gdp_fy22 * (1 + V["gdp_nominal_growth"]) ** (y - 2022) for y in range(2022, 2048)})


# ---------------------------------------------------------------------------
# 3. COST SCHEDULE of the three funded levers
# ---------------------------------------------------------------------------
def cost_schedule(premium0):
    base_cov = V["eshram_pmjay_linked_cr"] / V["eshram_registered_cr"]
    cov = []
    for y in YEARS:
        if y == 2027:
            c = base_cov + (V["uhc_target_2028"] - base_cov) * 0.5  # half-way to the 2027 target
        elif y == 2028:
            c = V["uhc_target_2028"]
        else:
            c = V["uhc_target_2028"] + (V["uhc_target_2047"] - V["uhc_target_2028"]) * (y - 2028) / (2047 - 2028)
        cov.append(c)
    cov = np.array(cov)
    extra_people_cr = (cov - base_cov) * V["eshram_registered_cr"]
    premium = premium0 * (1 + V["premium_inflation"]) ** (YEARS - 2027)
    uhc = extra_people_cr * premium  # crore people x Rs = Rs crore
    digital = np.where(YEARS < 2027 + V["digital_years"], V["digital_total_cr"] / V["digital_years"], 0.0)
    fund = np.where(YEARS < 2027 + V["fund_years"], V["fund_total_cr"] / V["fund_years"], 0.0)
    df = pd.DataFrame({
        "fy": YEARS, "digital_health": digital, "pandemic_fund": fund, "uhc_expansion": uhc,
        "uhc_coverage_of_eshram": cov, "extra_people_covered_cr": extra_people_cr,
    })
    df["total"] = df.digital_health + df.pandemic_fund + df.uhc_expansion
    df["gdp"] = [gdp[y] for y in YEARS]
    df["total_pct_gdp"] = df.total / df.gdp * 100
    return df


cs = cost_schedule(V["premium_per_person_fy27"])
cs.to_csv(os.path.join(RES, "cost_schedule.csv"), index=False)

# premium scenarios
scen_rows = []
for name, prem in [("low", 300), ("base", V["premium_per_person_fy27"]), ("high", 1000)]:
    d = cost_schedule(prem)
    scen_rows.append(dict(scenario=name, premium_fy27=prem, cumulative_cost_lakh_cr=d.total.sum() / 1e5,
                          peak_pct_gdp=d.total_pct_gdp.max(), fy2030_cost_cr=float(d.loc[d.fy == 2030, "total"].iloc[0]),
                          uhc_cumulative_lakh_cr=d.uhc_expansion.sum() / 1e5))
scen = pd.DataFrame(scen_rows)
scen.to_csv(os.path.join(RES, "cost_scenarios.csv"), index=False)

# ---------------------------------------------------------------------------
# 4. BENEFIT-COST: pandemic hedge, break-even analysis
# ---------------------------------------------------------------------------
disc = (1 + V["discount_nominal"]) ** -(YEARS - 2026)
pv_gdp = float((cs.gdp * disc).sum())
pv_cost_total = float((cs.total * disc).sum())
pv_cost_prep = float(((cs.digital_health + cs.pandemic_fund) * disc).sum())  # preparedness-only levers


def bcr(pv_cost, p, avoided_pp):
    return p * (avoided_pp / 100) * pv_gdp / pv_cost


probs = [0.005, 0.01, 0.02, 0.03, 0.05]
avoid = [0.5, 1.0, 1.5, 2.0, 3.0]
grid = pd.DataFrame([[bcr(pv_cost_prep, p, a) for a in avoid] for p in probs],
                    index=[f"{p*100:.1f}%" for p in probs], columns=[f"{a} pp" for a in avoid])
grid.index.name = "annual_shock_probability"
grid.to_csv(os.path.join(RES, "bcr_grid_preparedness_levers.csv"))
breakeven_pp = {f"{p*100:.1f}%": pv_cost_prep / (p * pv_gdp / 100) for p in probs}
breakeven_total_pp = {f"{p*100:.1f}%": pv_cost_total / (p * pv_gdp / 100) for p in probs}

# ---------------------------------------------------------------------------
# 5. RELIEF vs FUND: how far does Rs 1 lakh crore go?
# ---------------------------------------------------------------------------
amts, months = [2000, 3000, 5000], [2, 3, 6]
relief = pd.DataFrame([[V["eshram_registered_cr"] * a * m / 1e5 for m in months] for a in amts],
                      index=[f"Rs {a:,}/month" for a in amts], columns=[f"{m} months" for m in months])
relief.index.name = "transfer"
relief.to_csv(os.path.join(RES, "relief_cost_lakh_cr.csv"))
relief_base = V["eshram_registered_cr"] * V["relief_amount"] * V["relief_months"]
fund_months_cover = V["fund_total_cr"] / (V["eshram_registered_cr"] * V["relief_amount"])

# ---------------------------------------------------------------------------
# 6. OOP: what does the "up to 40% cost reduction" claim imply?
# ---------------------------------------------------------------------------
oop_fy22 = V["oop_share_fy22"] * V["the_fy22"]
oop_rows = []
for r in [0.10, V["pmjay_oop_reduction"], 0.40]:
    saved = oop_fy22 * r
    oop_rows.append(dict(reduction=r, saving_cr_fy22=saved, saving_lakh_cr=saved / 1e5,
                         new_oop_share_of_the=V["oop_share_fy22"] * (1 - r),
                         extra_public_spend_pct_gdp=saved / gdp_fy22 * 100,
                         ghe_pct_gdp_if_publicly_financed=V["ghe_gdp_share_fy22"] * 100 + saved / gdp_fy22 * 100))
oop = pd.DataFrame(oop_rows)
oop.to_csv(os.path.join(RES, "oop_sensitivity.csv"), index=False)

# ---------------------------------------------------------------------------
# 7. DOCTORS: what does 1.5 / 1,000 by 2047 require?
# ---------------------------------------------------------------------------
pop = {y: V["pop_2022_bn"] * (V["pop_2047_bn"] / V["pop_2022_bn"]) ** ((y - 2022) / 25) for y in range(2022, 2048)}
dens22 = V["alloc_doctors_2022"] / (pop[2022] * 1e9) * 1000
need_2047 = V["doctor_target_2047"] * pop[2047] * 1e9 / 1000
net_adds_total = need_2047 - V["alloc_doctors_2022"]
cagr = (need_2047 / V["alloc_doctors_2022"]) ** (1 / 25) - 1
docs = pd.DataFrame({"year": list(range(2022, 2048))})
docs["population_bn"] = docs.year.map(pop)
docs["available_doctors"] = V["alloc_doctors_2022"] * (need_2047 / V["alloc_doctors_2022"]) ** ((docs.year - 2022) / 25)
docs["per_1000"] = docs.available_doctors / (docs.population_bn * 1e9) * 1000
docs.to_csv(os.path.join(RES, "doctor_path.csv"), index=False)
official_density = V["alloc_doctors_2022"] / (124e7) * 1000  # govt used ~124 crore population

# ---------------------------------------------------------------------------
# 8. CHARTS
# ---------------------------------------------------------------------------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

# 8a. cost stack
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
x = cs.fy.values
b = np.zeros(len(x))
for col, lab, colr in [("digital_health", "Digital health (Rs 50,000 cr over 5 yrs)", C_BLUE),
                       ("pandemic_fund", "Pandemic Preparedness Fund (Rs 1 lakh cr over 10 yrs)", C_ORANGE),
                       ("uhc_expansion", "UHC expansion for informal workers", C_TEAL)]:
    ax.bar(x, cs[col] / 1e3, bottom=b, color=colr, label=lab, width=0.78, edgecolor="white", linewidth=0.8)
    b += cs[col].values / 1e3
style(ax)
ax.set_ylabel("Rs '000 crore per year (nominal)", color=INK)
ax.set_title("Annual cost of the paper's three funded levers, FY2027-FY2047", loc="left", color=INK, fontsize=12)
ax.legend(frameon=False, loc="upper right", fontsize=8.5)
ax.set_xticks(x[::2])
ax.set_ylim(0, 31)
pk = cs.loc[cs.total_pct_gdp.idxmax()]
ax.text(0.01, 0.97, f"Peak: {pk.total_pct_gdp:.3f}% of GDP (FY{int(pk.fy)})", transform=ax.transAxes, va="top", color=INK, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(RES, "01_annual_cost.png"))
plt.close(fig)

# 8b. BCR heatmap
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
im = ax.imshow(grid.values, cmap="Blues", vmin=0, vmax=4.0, aspect="auto")  # colour clipped at 4 so the 1.0 boundary stays visible
ax.set_xticks(range(len(avoid)), grid.columns)
ax.set_yticks(range(len(probs)), grid.index)
for i in range(len(probs)):
    for j in range(len(avoid)):
        v = grid.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v > 2.6 else INK, fontweight="bold" if v >= 1 else "normal", fontsize=9)
ax.set_xlabel("GDP loss avoided per pandemic (percentage points of a 9 pp shock)")
ax.set_ylabel("Annual probability of a COVID-scale shock")
ax.set_title("Benefit-cost ratio of digital health + preparedness fund\n(bold = pays for itself on pandemic benefits alone)", loc="left", fontsize=11, color=INK)
for s in ax.spines.values():
    s.set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(RES, "02_benefit_cost_heatmap.png"))
plt.close(fig)

# 8c. relief vs fund
fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=200)
w = 0.26
for k, (a, colr) in enumerate(zip(amts, [C_TEAL, C_BLUE, C_ORANGE])):
    vals = relief.iloc[k].values
    xs = np.arange(len(months)) + (k - 1) * w
    ax.bar(xs, vals, width=w - 0.02, color=colr, label=f"Rs {a:,} per worker per month")
    for xi, v in zip(xs, vals):
        ax.text(xi, v + 0.05, f"{v:.1f}", ha="center", fontsize=8, color=INK)
ax.axhline(V["fund_total_cr"] / 1e5, color=INK, linestyle="--", linewidth=1.2, label="Pandemic Preparedness Fund = Rs 1 lakh cr")
ax.set_xticks(range(len(months)), [f"{m}-month lockdown" for m in months])
ax.set_ylabel("Rs lakh crore", color=INK)
ax.set_title("Cost of relief for all 31.4 crore e-Shram workers vs the fund", loc="left", fontsize=12, color=INK)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
style(ax)
fig.tight_layout()
fig.savefig(os.path.join(RES, "03_relief_vs_fund.png"))
plt.close(fig)

# 8d. doctors
fig, ax = plt.subplots(figsize=(8.4, 4.4), dpi=200)
ax.plot(docs.year, docs.per_1000, color=C_BLUE, linewidth=2)
ax.axhline(1.0, color=C_GREY, linestyle="--", linewidth=1)
ax.text(2022.2, 1.02, "WHO norm: 1.0 per 1,000", fontsize=8.5, color=INK, va="bottom")
ax.scatter([2022, 2047], [dens22, V["doctor_target_2047"]], color=C_BLUE, zorder=3, s=36)
ax.annotate(f"{dens22:.2f} (2022, on 1.41 bn people)", (2022, dens22), xytext=(2023.2, dens22 - 0.12), fontsize=9, color=INK)
ax.text(2046.6, 1.56, "1.5 target (2047)", ha="right", fontsize=9, color=INK)
ax.set_ylim(0.5, 1.8)
ax.set_ylabel("Available allopathic doctors per 1,000", color=INK)
ax.set_title(f"Path to 1.5 doctors per 1,000: ~{net_adds_total/25/1e3:.0f}k net additions a year", loc="left", fontsize=12, color=INK)
style(ax)
fig.tight_layout()
fig.savefig(os.path.join(RES, "04_doctor_path.png"))
plt.close(fig)

# ---------------------------------------------------------------------------
# 9. SUMMARY + PARAMETER REGISTER
# ---------------------------------------------------------------------------
base_cov = V["eshram_pmjay_linked_cr"] / V["eshram_registered_cr"]
summary = {
    "gdp_fy22_lakh_cr_derived": gdp_fy22 / 1e5,
    "gdp_fy27_lakh_cr_projected": gdp[2027] / 1e5,
    "cumulative_cost_fy27_47_lakh_cr": cs.total.sum() / 1e5,
    "cumulative_by_lever_lakh_cr": {k: cs[k].sum() / 1e5 for k in ["digital_health", "pandemic_fund", "uhc_expansion"]},
    "fy2027_cost_cr": float(cs.total.iloc[0]), "fy2027_pct_gdp": float(cs.total_pct_gdp.iloc[0]),
    "peak_pct_gdp": float(cs.total_pct_gdp.max()), "peak_fy": int(pk.fy),
    "uhc_baseline_coverage_eshram": base_cov,
    "uhc_extra_people_by_fy2028_cr": float(cs.loc[cs.fy == 2028, "extra_people_covered_cr"].iloc[0]),
    "uhc_extra_people_by_fy2047_cr": float(cs.extra_people_covered_cr.iloc[-1]),
    "scenarios": scen.to_dict(orient="records"),
    "pv_cost_total_lakh_cr": pv_cost_total / 1e5, "pv_cost_preparedness_lakh_cr": pv_cost_prep / 1e5,
    "bcr_base_preparedness": bcr(pv_cost_prep, V["shock_prob"], V["loss_avoided_pp"]),
    "bcr_base_total_package": bcr(pv_cost_total, V["shock_prob"], V["loss_avoided_pp"]),
    "breakeven_pp_preparedness": breakeven_pp, "breakeven_pp_total": breakeven_total_pp,
    "relief_base_lakh_cr": relief_base / 1e5, "fund_covers_months_of_3000": fund_months_cover,
    "fund_as_share_of_base_relief": V["fund_total_cr"] / relief_base,
    "oop_fy22_lakh_cr": oop_fy22 / 1e5,
    "oop_sensitivity": oop.to_dict(orient="records"),
    "doctors": {"density_2022_recomputed": dens22, "density_2022_with_govt_population": official_density,
                "required_doctors_2047": need_2047, "net_adds_total": net_adds_total,
                "net_adds_per_year": net_adds_total / 25, "cagr": cagr},
    "covid_gdp_actual": {"provisional": V["covid_gdp_fy21_provisional"], "revised": V["covid_gdp_fy21_revised"]},
}
with open(os.path.join(RES, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2, default=float)

pd.DataFrame([dict(parameter=k, **v) for k, v in P.items()]).to_csv(os.path.join(DATA, "assumptions.csv"), index=False)

if __name__ == "__main__":
    print(json.dumps(summary, indent=2, default=float))
