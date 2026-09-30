# Wealth NYC

Compare New York City income in tax records and Census data. Both map views show annual averages per Census household for 2018–2022, in 2022 dollars, on one shared dollar scale.

A [publicworks.nyc](https://publicworks.nyc/) project, published at [wealth.publicworks.nyc](https://wealth.publicworks.nyc/). The map fills one viewport beneath the masthead. Desktop controls use a side panel. Phones use compact source selection and search above the map; selecting an area opens a full-screen card with a Back to map button. Mobile map notes, rotation controls, and the status strip are omitted; the Data page retains the methods and citations. Data and About use the shared Public Works footer.

## Data sources

IRS Statistics of Income ZIP files, tax years 2018–2022; ACS five-year estimates, 2018–2022; BLS annual CPI-U indexes; NYC Health MODZCTA boundaries; NYC Planning 2020 NTA names. Research downloads retain NYC Finance home sales, 2023–2025. Exact sources, dollar definitions, and original pull dates are in docs/data/meta.json and the Data page.

## Method and limits

Tax records: adjust each year's AGI (A00100 × 1,000) by CPI-U 2022 / CPI-U year, average the five annual totals, and divide by ACS households in the same mapped area. The new map field is irs_income_per_household_2022. This is a combined-source estimate, not returns linked to individual households.

Census: sum B19025 aggregate household income and B19001 households over the assigned ZCTAs, then divide. ACS already publishes these estimates in 2022 dollars; they are not adjusted again. The field is acs_mean_household_income, not the median.

Inflation uses BLS CUUR0000SA0 annual indexes: 251.107 (2018), 255.657 (2019), 258.811 (2020), 270.970 (2021), 292.655 (2022). Config and metadata preserve the indexes, formula, source, and verification date. Census retains its published adjustment procedure.

The two sources differ in definitions, filing addresses, survey coverage, and nonfilers. Their difference does not directly measure missing income or wealth. AGI includes reported realized gains, not unsold appreciation or net worth. The panel's investment share uses inflation-adjusted taxable interest + ordinary dividends + net capital gains over adjusted AGI.

Original per-return IRS research fields and the supplementary concentration chart remain nominal; new real-dollar fields end in _2022. Downloads retain high-income-return statistics, Census medians with margins, and research sales fields. They are not map layers.

177 NYC Health modified ZIP areas approximate postal ZIPs. Mostly Nassau ZCTAs 11001, 11003, 11040 and catch-all 99999 are excluded. IRS measures are withheld below 1,000 latest-year returns. Both map views use the same assigned Census household counts; representative-ZCTA medians in the research download are separate.

Stack height is linear and fixed in map units across zoom. Both views use the same height scale and color stops ($0, $100k, $300k, $1.2m). Color spacing is nonlinear; stack volume is not a money measure. Richer areas use brighter greens. Hover turns soft gold; selection turns saturated gold. Depth-tested boundaries follow stack tops, with softer outlines during zoom. Rotate the map or use Flat view to reach areas behind tall stacks; the compass resets north. Selection replaces the introductory copy with one card showing both sources and investment measures. Switching sources changes the map and preserves the card. Source, view, and selected area are preserved in the URL. Use the Data table for cross-area review.

## Updates

Use Python 3 with the dependencies in requirements.txt:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

The pipeline uses cached source files where available. For an annual update, verify available years, edit pipeline/00_config.py, and run `.venv/bin/python run.py --force-fetch`. Check the methods and years in the pages too. Initial fetches stream large national files and keep New York rows. Checks run before export. Never change a pull date just because output files were rebuilt.

Preview:

```sh
python3 -m http.server 8792 --directory docs --bind 127.0.0.1
```

Open http://127.0.0.1:8792. The production site is all of docs/, with no build step.

GitHub Pages publishes the `main` branch's `/docs` folder, following the other Public Works static sites. `docs/CNAME` sets `wealth.publicworks.nyc`; its DNS CNAME points to `jaramana.github.io`. `docs/.nojekyll` serves the files directly. Push changes to `main` to publish. Data updates are run manually with the pipeline above; there is no scheduled refresh.

## Tools

A static website with MapLibre GL JS and a Python data pipeline using pandas, requests, and Shapely. It uses no account system or analytics. Claude was used for the initial version. Codex was used for this rebuild.

## Verification

Run `python3 tests/check_data.py` after the pipeline. It independently reproduces the inflation-adjusted IRS map values, Census means and household denominators, investment shares, legacy nominal figures, and download parity.

For browser checks, serve docs/ on port 8792. Install puppeteer-core in a temporary tools folder, then set `PUPPETEER_MODULE` to that module path and `CHROME_PATH` to a Chrome executable before running `node tests/check_ui.cjs`. Screenshots go to `/tmp/wealth-qa` unless `QA_OUTPUT` is set. `QA_URL` can override the preview URL. Verification used puppeteer-core 23.11.1; Python dependencies were pandas 3.0.6, requests 2.34.2, and Shapely 2.1.2.

## License and reuse

Code: BSD 3-Clause (LICENSE). Source data retain their publishers' terms. Include the measure, unit, years, geographic coverage, publisher, and method with reused figures. CSV, GeoJSON, and a field guide are available on the Data page.
