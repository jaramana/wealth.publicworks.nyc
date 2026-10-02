"""Wealth NYC (wealth.publicworks.nyc): configuration.

Paths, sources, thresholds and labels live here. Later stages import them
and do not hard-code a URL, a year or a cutoff.
"""

from pathlib import Path

# ---- Paths -----------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

RAW = ROOT / "data-raw"        # cached downloads, not committed
BUILD = ROOT / "build"         # tables between stages, not committed
DOCS = ROOT / "docs"           # the published site
SITE_DATA = DOCS / "data"      # files the site reads and visitors download

for _d in (RAW, BUILD):
    _d.mkdir(parents=True, exist_ok=True)


# ---- Years -----------------------------------------------------------------
# The ACS five-year window matches the IRS tax years, so the two sources
# describe the same five years.

IRS_YEARS = [2018, 2019, 2020, 2021, 2022]
ACS_YEAR = 2022                # 2018-2022 five-year estimates
SALES_YEARS = [2023, 2024, 2025]

# BLS CPI-U, U.S. city average, all items, annual averages (CUUR0000SA0).
# Adjust each tax year's income before pooling; ACS already reports 2022 dollars.
CPI_U = {2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655}
CPI_SOURCE = "https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexannualandsemiannual_table.htm"
CPI_VERIFIED = "2026-09-29"


# ---- Sources ---------------------------------------------------------------
# `url` is what the pipeline fetches. `page` is where a person should look.

SOCRATA = "https://data.cityofnewyork.us"
ACS_SF = (
    "https://www2.census.gov/programs-surveys/acs/summary_file/"
    f"{ACS_YEAR}/table-based-SF/data/5YRData"
)

SOURCES = {
    "irs": {
        "publisher": "Internal Revenue Service, Statistics of Income",
        "title": "Individual Income Tax Statistics, ZIP Code Data",
        "page": "https://www.irs.gov/statistics/soi-tax-stats-individual-income-tax-statistics-zip-code-data-soi",
        "urls": {y: f"https://www.irs.gov/pub/irs-soi/{y % 100:02d}zpallagi.csv" for y in IRS_YEARS},
        "covers": f"Tax years {IRS_YEARS[0]}-{IRS_YEARS[-1]}",
    },
    "acs": {
        "publisher": "U.S. Census Bureau",
        "title": f"American Community Survey 5-year estimates, {ACS_YEAR - 4}-{ACS_YEAR}",
        "page": "https://www.census.gov/programs-surveys/acs/data/summary-file.html",
        "tables": {
            "b01003": "Total population",
            "b19001": "Household income in the past 12 months",
            "b19013": "Median household income",
            "b19025": "Aggregate household income",
            "b25002": "Occupancy status",
            "b25004": "Vacancy status",
            "b14002": "School enrollment by level and type of school",
            "b25003": "Tenure",
            "b25064": "Median gross rent",
        },
        "covers": f"Survey years {ACS_YEAR - 4}-{ACS_YEAR}",
    },
    "sales": {
        "publisher": "NYC Department of Finance",
        "title": "NYC Citywide Annualized Calendar Sales Update",
        "dataset_id": "w2pb-icbu",
        "page": f"{SOCRATA}/d/w2pb-icbu",
        "covers": f"Sales dated {SALES_YEARS[0]}-{SALES_YEARS[-1]}",
    },
    "modzcta": {
        "publisher": "NYC Department of Health and Mental Hygiene",
        "title": "Modified Zip Code Tabulation Areas (MODZCTA)",
        "dataset_id": "pri4-ifjk",
        "page": f"{SOCRATA}/d/pri4-ifjk",
        "covers": "Boundaries",
    },
    "nta": {
        "publisher": "NYC Department of City Planning",
        "title": "2020 Neighborhood Tabulation Areas (NTAs)",
        "dataset_id": "9nt8-h7nd",
        "page": f"{SOCRATA}/d/9nt8-h7nd",
        "covers": "Boundaries",
    },
}


# ---- IRS fields ------------------------------------------------------------
# Amounts are in thousands of dollars. Return counts are rounded to 10.

IRS_FIELDS = {
    "N1": "returns",
    "A00100": "agi",
    "A00200": "wages",
    "A00300": "interest",
    "A00600": "dividends",
    "A01000": "capital_gains",
    "A26270": "partnership",
    "A18500": "property_tax",
    "N01000": "n_capital_gains",
}
IRS_TOP_STUB = 6               # AGI $200,000 or more


# ---- Sales rules -----------------------------------------------------------
# Single dwellings: one-to-three family homes, co-ops and condos.
# Rental buildings, land, parking and commercial property are left out.

SALES_CLASSES = ("01", "02", "03", "04", "09", "10", "12", "13", "15", "17")
SALES_MIN_PRICE = 100_000      # lower sales are mostly transfers between relatives
SALES_MIN_COUNT = 20           # fewer sales and the ZIP gets no median


# ---- Crosswalk -------------------------------------------------------------
# MODZCTA lists some ZCTAs that lie mostly in Nassau County. Their whole
# ZIP totals would count Nassau filers as city filers, so they are left out.

EXCLUDE_ZCTAS = {"11001", "11003", "11040"}


# ---- Publication rules -----------------------------------------------------

MIN_RETURNS = 1_000            # comparison publication threshold; includes small residential areas

# Regional settings keep the calculation and website code in parity with Wealth NJ.
REGION = "nyc"
STATE_FIPS = "36"
CACHE_SUFFIX = "ny"
GROUP_FIELD = "borough"
DATA_STEM = "wealth-nyc-zip"
EXPECTED_AREAS = (170, 185)
MIN_PUBLISHED = 170
MIN_POPULATION = 8_000_000
