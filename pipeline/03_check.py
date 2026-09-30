"""Stage 3: check the ZIP table before anything is published.

Each check guards against a silent upstream change. One failure stops the run.
"""

import sys

import pandas as pd

cfg = sys.modules["00_config"]

SHARES = [
    "irs_capital_share_of_agi", "irs_top_share_of_returns", "irs_top_share_of_agi",
    "acs_share_households_200k", "acs_seasonal_share_of_units", "acs_private_share_k12",
    "irs_share_of_city_capital_income", "irs_share_of_city_returns", "acs_renter_share",
]


def run():
    t = pd.read_csv(cfg.BUILD / "zips.csv", dtype={"zip": str})
    problems = []

    def check(ok, message):
        if not ok:
            problems.append(message)

    check(170 <= len(t) <= 185, f"expected about 177 areas, found {len(t)}")
    check(t.zip.is_unique, "ZIP areas repeat")
    check(t.irs_published.sum() >= 170, f"only {t.irs_published.sum()} areas have IRS figures")
    check(t.name.notna().all(), "an area has no neighborhood name")
    check(t.acs_population.sum() > 8_000_000, "city population is under 8 million")
    check(t.sales_count.sum() > 100_000, f"only {t.sales_count.sum()} sales")
    check(t.acs_median_household_income.notna().sum() >= 170, "median income is missing for many areas")
    for field in ["irs_income_per_household_2022", "acs_mean_household_income"]:
        check(t[field].gt(0).sum() >= 170, f"missing or nonpositive map values: {field}")
    check((t.acs_households > 0).all(), "household denominator must be positive")
    check((t.irs_investment_share_2022.dropna().between(0, 1)).all(), "real investment shares outside 0–1")

    for c in SHARES:
        v = t[c].dropna()
        check(((v >= 0) & (v <= 1)).all(), f"{c} falls outside 0-1")

    for c in ["irs_share_of_city_capital_income", "irs_share_of_city_returns", "irs_share_of_city_investment_2022"]:
        check(abs(t[c].sum() - 1) < 0.001, f"{c} does not sum to 1")

    included = {z for zs in t.zips_included for z in zs.split(", ")}
    check(not included & cfg.EXCLUDE_ZCTAS, "a Nassau ZCTA is in the crosswalk")
    check({"11249", "11211"} <= included, "Williamsburg ZIPs are missing from the crosswalk")

    top = t.irs_top_agi_per_return.dropna()
    check((top >= 200_000).all(), "a top-bracket average is under $200,000")

    if problems:
        raise SystemExit("Checks failed:\n  " + "\n  ".join(problems))
    print(f"  {len(t)} areas pass")
