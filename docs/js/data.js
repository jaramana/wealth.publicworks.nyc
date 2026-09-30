import {
  $,
  money,
  percent,
  escapeHTML as esc,
  layers,
  loadJSON,
  period,
  chrome,
} from "./common.js?v=20260930";
chrome();
let rows = [];
function render() {
  const query = $("filter").value.trim().toLowerCase(),
    sort = $("sort").value;
  const filtered = rows.filter((p) =>
    `${p.zip} ${p.zips_included} ${p.name} ${p.borough}`
      .toLowerCase()
      .includes(query),
  );
  filtered.sort((a, b) =>
    layers[sort]
      ? (b[layers[sort].field] ?? -Infinity) -
          (a[layers[sort].field] ?? -Infinity) || a.zip.localeCompare(b.zip)
      : a[sort].localeCompare(b[sort]),
  );
  $("row-count").textContent = `${filtered.length} of ${rows.length} areas`;
  $("rows").innerHTML =
    filtered
      .map(
        (p) =>
          `<tr><td><a href="index.html#layer=${layers[sort] ? sort : "tax"}&zip=${esc(p.zip)}">${esc(p.zip)} · ${esc(p.name)}</a><small>${esc(p.borough)} · ZIPs ${esc(p.zips_included)}</small></td><td class="numeric">${money(p.irs_income_per_household_2022)}</td><td class="numeric">${money(p.acs_mean_household_income)}</td><td class="numeric">${percent(p.irs_investment_share_2022)}</td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="4">No matching areas. Try a ZIP code or borough.</td></tr>';
}
async function init() {
  try {
    const [data, meta] = await Promise.all([
      loadJSON("data/wealth-nyc-zip.geojson"),
      loadJSON("data/meta.json"),
    ]);
    rows = data.features.map((f) => f.properties);
    const c = meta.city;
    $("concentration-copy").textContent =
      `The ${c.top_areas} ZIP areas with the highest investment income per tax return account for ${percent(c.top_returns_share)} of mapped returns and ${percent(c.top_capital_share)} of mapped investment income.`;
    $("concentration-chart").innerHTML =
      `<div class="bar-label"><span>Those areas’ share of tax returns</span><strong>${percent(c.top_returns_share)}</strong></div><div class="bar"><span style="width:${c.top_returns_share * 100}%"></span></div><div class="bar-label"><span>Their share of investment income</span><strong>${percent(c.top_capital_share)}</strong></div><div class="bar"><span style="width:${c.top_capital_share * 100}%"></span></div><figcaption>Same ${c.top_areas} areas in both bars. IRS, ${period(meta)} pooled · Original-year dollars. The map uses 2022 dollars.</figcaption>`;
    $("data-vintage").textContent =
      `${rows.length} areas · IRS ${period(meta)} · ACS ${period(meta, "acs")} · Data built ${meta.built}`;
    document
      .querySelectorAll(".table-period")
      .forEach((el) => (el.textContent = period(meta)));
    $("citation").textContent =
      `Suggested citation: Wealth NYC, annual income per household, IRS and Census Bureau ${period(meta)}, in 2022 dollars, mapped to NYC Health MODZCTAs. IRS source files last pulled ${meta.sources.irs.pulled}. ${new URL("index.html", location.href).href.split("#")[0]}`;
    $("source-list").innerHTML = Object.values(meta.sources)
      .map(
        (s) =>
          `<article><h3><a href="${esc(s.page)}">${esc(s.title)}</a></h3><p>${esc(s.publisher)}</p><p>${esc(s.covers)} · Pulled ${esc(s.pulled)}</p></article>`,
      )
      .join("");
    $("field-rows").innerHTML = meta.fields
      .map(
        (f) =>
          `<tr><td><code>${esc(f.column)}</code></td><td>${esc(f.label)}<br><small>${esc(f.note)}</small></td><td>${esc(f.unit)}<br>${esc(meta.sources[f.source]?.publisher || f.source)}</td></tr>`,
      )
      .join("");
    $("filter").addEventListener("input", render);
    $("sort").addEventListener("change", render);
    render();
  } catch (error) {
    console.error(error);
    $("rows").innerHTML =
      '<tr><td colspan="4">The table could not load. Use the downloads above, or reload this page.</td></tr>';
    $("row-count").textContent = "Data unavailable";
  }
}
init();
