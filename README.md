# Wealth NYC

[Wealth NYC](https://wealth.publicworks.nyc) is an independent
[publicworks.nyc](https://publicworks.nyc) map that compares New York City income
in tax records and Census Bureau data. Both views show annual averages per Census
household for 2018–2022, in 2022 dollars, on one shared dollar scale.

## Data sources

| Source | Used for | Period |
| --- | --- | --- |
| [IRS Statistics of Income, ZIP Code Data](https://www.irs.gov/statistics/soi-tax-stats-individual-income-tax-statistics-zip-code-data-soi) | Adjusted gross income and investment income by ZIP | Tax years 2018–2022 |
| [Census Bureau American Community Survey](https://www.census.gov/programs-surveys/acs/data/summary-file.html) | Aggregate household income and household counts | 2018–2022 five-year estimates |
| BLS all-items CPI-U, `CUUR0000SA0` | Inflation adjustment to 2022 dollars | Annual averages, 2018–2022 |
| [NYC Health MODZCTA boundaries](https://data.cityofnewyork.us/d/pri4-ifjk) | The 177 map areas | Boundaries |
| [NYC Planning 2020 Neighborhood Tabulation Areas](https://data.cityofnewyork.us/d/9nt8-h7nd) | Neighborhood names | Boundaries |
| [NYC Finance annualized sales](https://data.cityofnewyork.us/d/w2pb-icbu) | Research downloads only | Sales dated 2023–2025 |

Exact sources, dollar definitions and pull dates are in `docs/data/meta.json`.
Source files were pulled on 28 September 2026; the data were rebuilt on 2 October 2026.

## Method and limits

- IRS map field `irs_income_per_household_2022`: adjust each year's AGI
  (`A00100` × 1,000) by CPI-U 2022 ÷ CPI-U for that year, average the five annual
  totals, and divide by ACS households in the same mapped area. This combines two
  sources and does not link returns to households.
- Census map field `acs_mean_household_income`: sum `B19025` aggregate household
  income and `B19001` households over the assigned ZCTAs, then divide. ACS already
  publishes these in 2022 dollars, so they are not adjusted again. The field is
  the mean, not the median.
- Inflation uses BLS `CUUR0000SA0` annual indexes: 251.107 (2018), 255.657
  (2019), 258.811 (2020), 270.970 (2021) and 292.655 (2022). `meta.json` keeps the
  indexes, formula and verification date.
- The two sources differ in definitions, filing addresses, survey coverage and
  nonfilers, so their difference does not measure missing income or wealth. AGI
  includes reported realized gains, not unsold appreciation or net worth.
- The 177 areas approximate postal ZIPs. Mostly Nassau ZCTAs 11001, 11003 and
  11040 and the catch-all 99999 are excluded. IRS measures are withheld below 1,000
  latest-year returns or without all five tax years. This is our publication rule, not an IRS confidentiality threshold.
- Stack height is linear at a fixed map scale, and both views share color stops at
  $0, $100k, $300k and $1.2m. Original per-return IRS fields and the concentration
  chart stay in nominal dollars. New real-dollar fields end in `_2022`. Color saturates above $1.2m; height continues linearly. Missing values have a separate legend key.

The [Data page](https://wealth.publicworks.nyc/data.html) has the calculations,
limits, a sortable table and the field definitions.

## Updates

The pipeline runs by hand and has no scheduled refresh. Use Python 3 with the
dependencies in `requirements.txt`:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

The pipeline uses cached source files where available. For an annual update,
check the available years, edit `pipeline/00_config.py` and run
`.venv/bin/python run.py --force-fetch`. Then check the years and methods in the
pages. Large national files stream in and only New York rows are kept. Checks run
before export. Never change a pull date because output files were rebuilt.

To preview the site, which is all of `docs/` with no build step:

```sh
python3 -m http.server 8792 --directory docs --bind 127.0.0.1
```

Open http://127.0.0.1:8792. GitHub Pages publishes the `main` branch's `/docs`
folder. `docs/CNAME` sets `wealth.publicworks.nyc` and `docs/.nojekyll` serves the
files directly. Push to `main` to publish.

## Tools

Data pipeline: Python, `pandas`, `requests` and `Shapely`. Website: static HTML,
CSS and JavaScript, served from GitHub Pages, with MapLibre GL JS. The site uses
no account system or analytics. Claude and Codex were used in development.

## Verification

Run `python3 tests/check_data.py` after the pipeline. It independently reproduces
the inflation-adjusted IRS values, Census means and household denominators,
investment shares, legacy nominal figures, missing/withheld values, ACS margins and download parity.

For browser checks, serve `docs/` on port 8792. Install `puppeteer-core` in a
temporary tools folder, set `PUPPETEER_MODULE` to that module path and
`CHROME_PATH` to a Chrome executable, then run `node tests/check_ui.cjs`.
Screenshots go to `/tmp/wealth-qa` unless `QA_OUTPUT` is set, and `QA_URL`
overrides the preview address. The browser tooling uses puppeteer-core 23.11.1. Python dependencies are pinned to the verified versions: pandas
3.0.6, requests 2.34.2 and Shapely 2.1.2.

## License and reuse

Code is [BSD 3-Clause licensed](LICENSE). Source data retain their publishers'
terms. Include the measure, unit, years, geography, publisher and method with
reused figures. The CSV, GeoJSON and field definitions are on the Data page.

## Regional parity

[Wealth NJ](https://wealthnj.publicworks.nyc/) lives in the sibling
`wealthnj.publicworks.nyc` repository. Both sites use identical map, table,
formatting, roof-outline, styling and calculation modules. Regional labels,
search fields and camera framing live in `docs/js/site-config.js`; source and
coverage rules live in `pipeline/00_config.py`. NYC retains its MODZCTA geography,
original field names and research-only property-sales fields. NJ uses Census
ZCTAs, municipalities and counties, with state shares.

Run `python3 tests/check_parity.py ../wealthnj.publicworks.nyc` to check shared
files after editing. Carry shared fixes to both repositories. The independent
source checks require each repository's own raw cache. `run.py --stage 4` checks
the intermediate table before exporting. See `REVIEW.md` for the October 2026
content and methodology review.
