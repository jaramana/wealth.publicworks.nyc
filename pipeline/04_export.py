"""Stage 4: write the files the site reads and visitors download.

    docs/data/wealth-nyc-zip.csv       one row per ZIP area
    docs/data/wealth-nyc-zip.geojson   the same rows with simplified shapes
    docs/data/meta.json                sources, pull dates, fields, city figures
"""

import json
import sys
from datetime import date

import pandas as pd
from shapely.geometry import mapping, shape

cfg = sys.modules["00_config"]

SIMPLIFY = 0.00012             # degrees, about 12 meters
PRECISION = 5                  # decimal places, about 1 meter

# Field order here is column order in the downloads.
# Each entry: column, label, unit, source, note.

FIELDS = [
    ("irs_share_of_city_investment_2022", "Share of NYC investment income", "share", "irs", "Share of inflation-adjusted annual investment income in all mapped areas with published IRS figures. Same 2018–2022 years and 2022 dollars as the panel."),
    ("irs_income_per_household_2022", "Tax records: annual income per household", "dollars", "irs", "Annual average AGI, adjusted year by year to 2022 dollars using BLS CPI-U, divided by ACS households in the same mapped area. Combined-source estimate; returns are not linked to households."),
    ("irs_agi_annual_2022", "Annual average AGI, 2022 dollars", "dollars", "irs", "Sum of each year's AGI multiplied by CPI-U 2022 / CPI-U year, divided by five years."),
    ("irs_investment_annual_2022", "Annual average investment income, 2022 dollars", "dollars", "irs", "Taxable interest, ordinary dividends and net capital gains; each year adjusted using CPI-U, then averaged."),
    ("irs_investment_share_2022", "Investment share of reported income", "share", "irs", "Inflation-adjusted investment income divided by inflation-adjusted AGI across 2018–2022."),
    ("irs_returns_annual", "Annual average tax returns", "count", "irs", "Sum of returns for 2018–2022 divided by five. Not unique filers."),
    ("zip", "ZIP area", "text", "modzcta", "MODZCTA code. Some areas combine several ZIP codes."),
    ("name", "Neighborhood", "text", "nta",
     "Residential NTA that covers most of the area. Names can repeat; the ZIP is the identifier."),
    ("borough", "Borough", "text", "nta", ""),
    ("zips_included", "ZIP codes included", "text", "modzcta",
     "ZIPs joined to the area. Nassau ZCTAs 11001, 11003 and 11040 are left out."),
    ("irs_returns", "Tax returns", "count", "irs", "Returns filed for the latest tax year. Rounded to 10 by the IRS."),
    ("irs_agi_per_return", "Adjusted gross income per return", "dollars", "irs",
     "Five tax years pooled. Legacy research field in nominal dollars; not the household-normalized map measure."),
    ("irs_wages_per_return", "Wages per return", "dollars", "irs", "Five tax years pooled."),
    ("irs_capital_income_per_return", "Investment income per tax return", "dollars", "irs",
     "Taxable interest, ordinary dividends and net capital gains. Five tax years pooled."),
    ("irs_investment_income_annual", "Investment income, annual average total", "dollars", "irs", "Sum of taxable interest, ordinary dividends and net capital gains across all mapped returns, divided by the number of tax years."),
    ("irs_capital_gains_per_return", "Net capital gains per return", "dollars", "irs", "Five tax years pooled."),
    ("irs_partnership_per_return", "Partnership and S-corp income per return", "dollars", "irs", "Five tax years pooled."),
    ("irs_capital_share_of_agi", "Investment income share of AGI", "share", "irs", "Five tax years pooled."),
    ("irs_top_share_of_returns", "Returns with AGI of $200,000 or more", "share", "irs", "Five tax years pooled."),
    ("irs_top_agi_per_return", "Average AGI of returns at $200,000 or more", "dollars", "irs",
     "Five tax years pooled. Blank where the IRS suppressed the class."),
    ("irs_top_share_of_agi", "Share of AGI on returns at $200,000 or more", "share", "irs", "Five tax years pooled."),
    ("irs_share_of_city_capital_income", "Share of mapped investment income", "share", "irs", "Five tax years pooled."),
    ("irs_share_of_city_returns", "Share of mapped tax returns", "share", "irs", "Five tax years pooled."),
    ("acs_population", "Population", "count", "acs", ""),
    ("acs_households", "Households", "count", "acs", ""),
    ("acs_median_household_income", "Median household income", "dollars", "acs",
     f"Representative ZCTA median, not a combined-area median. In {cfg.ACS_YEAR} dollars. The Census reports 250,001 for any median above $250,000."),
    ("acs_median_household_income_moe", "Household income margin of error", "dollars", "acs", f"90% confidence margin for the median, from the representative ZCTA. In {cfg.ACS_YEAR} dollars. Blank when unavailable or top-coded."),
    ("acs_mean_household_income", "Census: average household income", "dollars", "acs", "ACS B19025 aggregate household income divided by B19001 households, summed over the assigned ZCTAs. Published in 2022 dollars; not adjusted again. Excludes capital gains."),
    ("acs_share_households_200k", "Households with income of $200,000 or more", "share", "acs",
     "Highest category in ACS table B19001. It has no upper edge."),
    ("acs_renter_share", "Households that rent", "share", "acs", ""),
    ("acs_median_gross_rent", "Median gross rent", "dollars", "acs",
     "Monthly rent plus utilities. The Census reports 3,501 for any median above $3,500."),
    ("acs_private_share_k12", "K-12 students in private school", "share", "acs",
     "Private includes religious schools. Charter schools count as public."),
    ("acs_seasonal_units", "Homes held for occasional use", "count", "acs",
     "Vacant units for seasonal, recreational or occasional use."),
    ("acs_seasonal_share_of_units", "Share of homes held for occasional use", "share", "acs", ""),
    ("sales_count", "Home sales", "count", "sales",
     "One-to-three family homes, co-ops and condos sold for $100,000 or more."),
    ("sales_median_price", "Median home sale price", "dollars", "sales", "Blank below 20 sales."),
    ("sales_over_5m", "Home sales of $5 million or more", "count", "sales", ""),
]


def city_figures(t):
    """Figures the story quotes. The page fills its sentences from these.

    Every group ranks areas the same way, by capital income per return.
    """
    ranked = t[t.irs_published].sort_values("irs_capital_income_per_return", ascending=False)
    cum_cap = ranked.irs_share_of_city_capital_income.cumsum()
    cum_ret = ranked.irs_share_of_city_returns.cumsum()
    half = int((cum_cap < 0.5).sum()) + 1     # fewest areas that hold half
    bottom = ranked.tail(len(t) // 2)

    gains = json.loads((cfg.BUILD / "gains_by_year.json").read_text())
    low, high = min(gains, key=gains.get), max(gains, key=gains.get)
    top = ranked.irs_top_agi_per_return.idxmax()

    return {
        "areas": len(t),
        "gains_low_year": int(low),
        "gains_low": gains[low],
        "gains_high_year": int(high),
        "gains_high": gains[high],
        "top_bracket_highest_zip": t.loc[top, "zip"],
        "top_areas": half,
        "top_capital_share": round(float(cum_cap.iloc[half - 1]), 4),
        "top_returns_share": round(float(cum_ret.iloc[half - 1]), 4),
        "bottom_areas": len(bottom),
        "bottom_half_capital_share": round(float(bottom.irs_share_of_city_capital_income.sum()), 4),
        "bottom_half_returns_share": round(float(bottom.irs_share_of_city_returns.sum()), 4),
        "median_topcoded_areas": int((t.acs_median_household_income >= 250_001).sum()),
    }


def rounded(v, unit):
    if pd.isna(v):
        return None
    if unit == "share":
        return round(float(v), 4)
    if unit in ("dollars", "count"):
        return int(round(float(v)))
    return v


def run():
    t = pd.read_csv(cfg.BUILD / "zips.csv", dtype={"zip": str})
    shapes = json.loads((cfg.BUILD / "shapes.json").read_text())
    cfg.SITE_DATA.mkdir(parents=True, exist_ok=True)

    columns = [f[0] for f in FIELDS]
    units = {f[0]: f[2] for f in FIELDS}
    out = t[columns].copy()
    for c in columns:
        out[c] = [rounded(v, units[c]) for v in out[c]]
    out = out.astype({c: "Int64" for c in columns if units[c] in ("dollars", "count")})
    out.to_csv(cfg.SITE_DATA / "wealth-nyc-zip.csv", index=False)

    features = []
    for row in out.to_dict("records"):
        geom = shape(shapes[row["zip"]]).simplify(SIMPLIFY, preserve_topology=True)
        geom = json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), PRECISION))
        props = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        features.append({"type": "Feature", "properties": props, "geometry": geom})
    (cfg.SITE_DATA / "wealth-nyc-zip.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
    )

    pulled = json.loads((cfg.RAW / "pulled.json").read_text())
    meta = {
        "built": date.today().isoformat(),
        "years": {"irs": cfg.IRS_YEARS, "acs": [cfg.ACS_YEAR - 4, cfg.ACS_YEAR], "sales": cfg.SALES_YEARS},
        "sources": {
            k: {"publisher": s["publisher"], "title": s["title"], "page": s["page"],
                "covers": s["covers"], "pulled": pulled.get(k)}
            for k, s in cfg.SOURCES.items()
        },
        "fields": [dict(zip(("column", "label", "unit", "source", "note"), f)) for f in FIELDS],
        "city": city_figures(t),
        "comparison": {
            "dollar_year": cfg.ACS_YEAR,
            "irs_formula": "sum(AGI_year * CPI_2022 / CPI_year) / 5 / ACS_households",
            "census_formula": "ACS_B19025_E001 / ACS_B19001_E001",
            "inflation": {"series": "CUUR0000SA0", "name": "CPI-U, U.S. city average, all items, annual averages", "annual_indexes": cfg.CPI_U, "source": cfg.CPI_SOURCE, "verified": cfg.CPI_VERIFIED},
            "note": "Both map layers use ACS household counts and 2022 dollars. IRS is a combined-source estimate, not linked household returns. Definitions and coverage differ; their difference is not a measure of missing income or wealth.",
            "legacy_fields": "Other IRS dollar fields and original concentration shares remain nominal unless their names end in _2022."
        },
        "source_files": json.loads((cfg.RAW / "pulled-files.json").read_text()) if (cfg.RAW / "pulled-files.json").exists() else {},
        "pull_date_note": "Source-level dates show the most recent successful file download; source_files records individual file dates. Original cache dates are inherited from its source-family record.",
        "coverage": {"unit": "NYC Health MODZCTA", "min_returns": cfg.MIN_RETURNS, "excluded_zctas": sorted(cfg.EXCLUDE_ZCTAS), "irs_published_areas": int(t.irs_published.sum()), "note": "City shares refer to mapped areas with published figures, not all NYC residents or returns."},
    }
    (cfg.SITE_DATA / "meta.json").write_text(json.dumps(meta, indent=2))

    size = (cfg.SITE_DATA / "wealth-nyc-zip.geojson").stat().st_size / 1e6
    print(f"  {len(out)} rows; map file {size:.1f} MB")
