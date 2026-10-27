export const analysisValue = {
  version: '1', status: 'ok', executed: true, items: [{
    oil_bbl_sum: '123.45', oil_bbl_sum_null_records: 0, source_records: 2,
    first_observation: '2025-01-01', last_observation: '2025-12-31',
  }],
  truncated: false, source: 'oge_synthetic.daily_production', units: { oil_bbl_sum: 'bbl' },
  source_grain: 'day', executed_at: '2026-10-26T20:00:00+00:00', joined_sources: [], notes: [],
  plan: {
    version: '1', dataset: 'production', start_date: '2025-01-01', end_date: '2025-12-31',
    measures: [{ field: 'oil_bbl', aggregation: 'sum' }], group_by: [], time_bucket: 'none',
    filters: [], order_by: null, limit: 100,
  },
};

export const contextValue = { version: '1', schema: 'oge_synthetic', datasets: {} };

// Structural representative of observed GA output; all business values are synthetic.
export const foundryOutput = (value: unknown) =>
  `${JSON.stringify(value)}\n${JSON.stringify({ structuredResponse: value })}`;
