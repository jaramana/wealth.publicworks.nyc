"""Independent checks of the published downloads against cached IRS source rows.
Run after python run.py: python tests/check_data.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data'
rows = list(csv.DictReader((DATA / 'wealth-nyc-zip.csv').open()))
meta = json.loads((DATA / 'meta.json').read_text())
features = json.loads((DATA / 'wealth-nyc-zip.geojson').read_text())['features']
assert len(rows) == len(features) == meta['city']['areas']
assert len({r['zip'] for r in rows}) == len(rows)
lookup = {}
for row in rows:
    for zipcode in row['zips_included'].split(', '):
        assert zipcode not in lookup, f'Duplicate postal ZIP: {zipcode}'
        assert zipcode not in {'11001', '11003', '11040', '99999'}
        lookup[zipcode] = row['zip']

sums = defaultdict(lambda: [0., 0.])
for year in meta['years']['irs']:
    with (ROOT / 'data-raw' / f'irs_{year}_ny.csv').open() as file:
        for source in csv.DictReader(file):
            source = {k.upper(): v for k, v in source.items()}
            zipcode = lookup.get(source['ZIPCODE'].zfill(5))
            if not zipcode:
                continue
            sums[zipcode][0] += sum(float(source[k]) for k in ['A00300', 'A00600', 'A01000']) * 1000
            sums[zipcode][1] += float(source['N1'])

for row, feature in zip(rows, features):
    assert row['zip'] == feature['properties']['zip']
    if row['irs_capital_income_per_return']:
        expected = sums[row['zip']][0] / sums[row['zip']][1]
        assert abs(float(row['irs_capital_income_per_return']) - expected) <= .51, row['zip']
    for field in meta['fields']:
        value = feature['properties'][field['column']]
        csv_value = row[field['column']]
        if value is None:
            assert csv_value == ''
        elif field['unit'] in ('dollars', 'count', 'share'):
            assert float(csv_value) == value
        else:
            assert csv_value == value

ranked = sorted((r for r in rows if r['irs_capital_income_per_return']), key=lambda r: float(r['irs_capital_income_per_return']), reverse=True)
all_dollars = sum(sums[r['zip']][0] for r in ranked)
all_returns = sum(sums[r['zip']][1] for r in ranked)
selected_dollars = selected_returns = 0
for number, row in enumerate(ranked, 1):
    selected_dollars += sums[row['zip']][0]
    selected_returns += sums[row['zip']][1]
    if selected_dollars / all_dollars >= .5:
        break
assert number == meta['city']['top_areas']
assert abs(selected_dollars / all_dollars - meta['city']['top_capital_share']) < .0001
assert abs(selected_returns / all_returns - meta['city']['top_returns_share']) < .0001
print(f'PASS: {len(rows)} source calculations, CSV/GeoJSON parity, crosswalk, and concentration shares.')

# Independently reconstruct the map comparison, including its shared household
# denominator and year-by-year inflation adjustment. Legacy nominal fields above
# deliberately retain their original contract.
cpi = {2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655}
assert meta['comparison']['inflation']['annual_indexes'] == {str(k): v for k, v in cpi.items()}
real = defaultdict(lambda: [0., 0., 0.])
for year in range(2018, 2023):
    for d in csv.DictReader((ROOT / 'data-raw' / f'irs_{year}_ny.csv').open()):
        d = {k.upper(): v for k, v in d.items()}
        z = lookup.get(d['ZIPCODE'].zfill(5))
        if z:
            real[z][0] += float(d['A00100']) * 1000 * cpi[2022] / cpi[year] / 5
            real[z][1] += sum(float(d[k]) for k in ['A00300', 'A00600', 'A01000']) * 1000 * cpi[2022] / cpi[year] / 5
            real[z][2] += float(d['N1']) / 5
acs = defaultdict(lambda: [0., 0.])
for i, table in enumerate(['b19001', 'b19025']):
    for d in csv.DictReader((ROOT / 'data-raw' / f'acs_2022_{table}_ny.dat').open(), delimiter='|'):
        z = lookup.get(d['GEO_ID'][-5:])
        value = d[table.upper() + '_E001']
        if z and value and float(value) >= 0:
            acs[z][i] += float(value)
for row in rows:
    z = row['zip']; households, income = acs[z]
    assert households > 0
    assert households == float(row['acs_households'])
    expected = {
        'irs_income_per_household_2022': real[z][0] / households,
        'irs_agi_annual_2022': real[z][0],
        'irs_investment_annual_2022': real[z][1],
        'irs_returns_annual': real[z][2],
        'acs_mean_household_income': income / households,
    }
    for field, value in expected.items():
        assert abs(float(row[field]) - value) <= .51, (z, field)
    assert abs(float(row['irs_investment_share_2022']) - real[z][1] / real[z][0]) < .000051
    assert float(row['irs_income_per_household_2022']) <= 1200000, 'Revisit shared map scale'
print(f'PASS: {len(rows)} inflation-adjusted IRS totals, household denominators, Census averages and investment shares.')

real_total = sum(real[r['zip']][1] for r in rows if r['irs_investment_annual_2022'])
for row in rows:
    assert abs(float(row['irs_share_of_city_investment_2022']) - real[row['zip']][1] / real_total) < .000051
assert abs(sum(float(r['irs_share_of_city_investment_2022']) for r in rows) - 1) < .002
print('PASS: normalized NYC investment-income shares.')
