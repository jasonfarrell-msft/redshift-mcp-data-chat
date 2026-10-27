export const dataQualityPrompt = `I ran the initial data-quality checks across the annual_production table and here are the results and next steps.

What I ran and results

- Total annual_production rows: 6,377.
- NULLs in key measures (oil_bbl, gas_mcf, operating_cost_usd): 0 rows.
- Negative values in those measures: 0 rows.
- Cases with months_with_records = 0 but oil_bbl > 0: 0 rows.
- Cases with days_with_production = 0 but oil_bbl > 0: 0 rows.

These checks show no obvious null/negative or simple completeness problems in the annual aggregates.

Suggested remaining outlier checks (I will run these if you confirm)

- A: Top / bottom annual oil producers (identify wells with unusually large or very small annual oil_bbl). SQL: SELECT production_year, state, basin, operator, oil_bbl FROM annual_production a JOIN wells w ON a.well_id = w.well_id ORDER BY a.oil_bbl DESC LIMIT 50;SELECT production_year, state, basin, operator, oil_bbl FROM annual_production a JOIN wells w ON a.well_id = w.well_id WHERE a.oil_bbl > 0 ORDER BY a.oil_bbl ASC LIMIT 50;
- B: Highest oil_bbl per reported production day (possible data entry or aggregation issues): SQL: SELECT production_year, state, basin, operator, oil_bbl, days_with_production, (oil_bbl / NULLIF(days_with_production,0)) AS oil_bbl_per_day FROM annual_production a JOIN wells w ON a.well_id = w.well_id WHERE a.days_with_production > 0 ORDER BY oil_bbl_per_day DESC LIMIT 50;
- C: Operating cost per barrel (cost anomalies): SQL: SELECT production_year, state, basin, operator, oil_bbl, operating_cost_usd, (operating_cost_usd / NULLIF(oil_bbl,0)) AS cost_per_bbl FROM annual_production a JOIN wells w ON a.well_id = w.well_id WHERE a.oil_bbl > 0 ORDER BY cost_per_bbl DESC LIMIT 50;
- D: Completeness flags (few months/days but positive volume): SQL: SELECT production_year, state, basin, operator, oil_bbl, months_with_records, days_with_production FROM annual_production a JOIN wells w ON a.well_id = w.well_id WHERE (a.months_with_records < 6 AND a.oil_bbl > 0) OR (a.days_with_production < 30 AND a.oil_bbl > 0) ORDER BY production_year DESC LIMIT 200;
- E: Price/revenue mismatches at monthly grain (optional monthly check): SQL: SELECT mp.production_month, state, basin, operator, mp.oil_bbl, mp.oil_bbl * mp_prices.oil_usd_per_bbl AS implied_revenue, mp_prices.oil_usd_per_bbl FROM monthly_production mp JOIN wells w ON mp.well_id = w.well_id LEFT JOIN monthly_prices mp_prices ON mp.production_month = mp_prices.price_month WHERE mp_prices.oil_usd_per_bbl IS NULL OR mp.oil_bbl IS NULL LIMIT 200;

A couple of quick preference questions before I run the remaining checks:

1. Do you want well_id included in the output for traceability? (Recommendation: include it for any outliers so you can inspect raw records \u2014 I can hide it in summary reports.)
2. How many rows should I return for each check? (Default: 50 for top lists, 200 for completeness lists.)
3. Run the monthly price/revenue check as well? (Y/N)`;
