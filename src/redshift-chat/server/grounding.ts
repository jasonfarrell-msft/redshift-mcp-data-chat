import { isDeepStrictEqual } from 'node:util';
import { CallToolResultSchema } from '@modelcontextprotocol/sdk/types.js';
import { AppError } from './contracts.js';

const NON_DATA = {
  clarification: {
    missing_period: 'Which inclusive date range should I analyze?',
    ambiguous_request: 'Please specify the metric, period, and any grouping or filters to analyze.',
  },
  unsupported: {
    unsupported_metric: 'That calculation is not supported. I can analyze production and operating-cost sums, well counts, or monthly price averages, minima and maxima.',
    unsupported_scope: 'That request is outside the supported synthetic analytics scope. Please ask about production, wells, or monthly prices.',
  },
} as const;

function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function fail(): never { throw new AppError(503, 'AGENT_UNAVAILABLE'); }

function parseFoundryBusinessOutput(output: string): Record<string, unknown> {
  const start = output.search(/[^ \t\r\n]/);
  if (start < 0 || output[start] !== '{') return fail();
  let depth = 0;
  let quoted = false;
  let escaped = false;
  for (let i = start; i < output.length; i++) {
    const char = output[i];
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') quoted = false;
    } else if (char === '"') quoted = true;
    else if (char === '{' || char === '[') depth++;
    else if (char === '}' || char === ']') {
      if (--depth !== 0) continue;
      // Find the root boundary, not a line: containers span lines and strings contain delimiters.
      if (!/[ \t\r\n]/.test(output[i + 1] ?? '')) return fail();
      const value: unknown = JSON.parse(output.slice(start, i + 1));
      const wrapper: unknown = JSON.parse(output.slice(i + 1));
      if (!object(value) || !object(wrapper) ||
          Object.keys(wrapper).length !== 1 || !Object.hasOwn(wrapper, 'structuredResponse') ||
          !object(wrapper.structuredResponse) ||
          !isDeepStrictEqual(value, wrapper.structuredResponse) ||
          ['content', 'structuredContent', 'isError', 'structuredResponse'].some((key) => key in value)) return fail();
      return value;
    }
  }
  return fail();
}

export function parseToolOutput(output: unknown): Record<string, unknown> {
  if (typeof output !== 'string' || Buffer.byteLength(output, 'utf8') > 256 * 1024) return fail();
  try {
    let value: unknown;
    try { value = JSON.parse(output); }
    catch { value = parseFoundryBusinessOutput(output); }
    if (!object(value)) return fail();
    // Foundry can return the business JSON directly or the official MCP CallToolResult.
    if ('content' in value || 'structuredContent' in value || 'isError' in value) {
      const envelope = CallToolResultSchema.parse(value);
      const content = envelope.content[0];
      if (envelope.isError || envelope.content.length !== 1 ||
          content?.type !== 'text') return fail();
      const text: unknown = JSON.parse(content.text);
      if (envelope.structuredContent !== undefined &&
          !isDeepStrictEqual(envelope.structuredContent, text)) return fail();
      if (!object(text)) return fail();
      return text;
    }
    return value;
  } catch { return fail(); }
}

const METRICS: Record<string, { unit: string; aggregations: string[]; dataset: string }> = {
  oil_bbl: { unit: 'bbl', aggregations: ['sum'], dataset: 'production' },
  gas_mcf: { unit: 'Mcf', aggregations: ['sum'], dataset: 'production' },
  operating_cost_usd: { unit: 'USD', aggregations: ['sum'], dataset: 'production' },
  oil_usd_per_bbl: { unit: 'USD/bbl', aggregations: ['avg', 'min', 'max'], dataset: 'prices' },
  gas_usd_per_mcf: { unit: 'USD/Mcf', aggregations: ['avg', 'min', 'max'], dataset: 'prices' },
  wells: { unit: 'wells', aggregations: ['count'], dataset: 'wells' },
};
const SOURCES: Record<string, [string, string]> = {
  'oge_synthetic.daily_production': ['production', 'day'],
  'oge_synthetic.monthly_production': ['production', 'month'],
  'oge_synthetic.annual_production': ['production', 'year'],
  'oge_synthetic.monthly_prices': ['prices', 'month'],
  'oge_synthetic.wells': ['wells', 'well'],
};
const count = (value: unknown): value is number => Number.isSafeInteger(value) && (value as number) >= 0;
const date = (value: unknown): value is string => typeof value === 'string' &&
  /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) &&
  new Date(value).toISOString().slice(0, 10) === value;

export function validateAnalysis(value: Record<string, unknown>) {
  const plan = value.plan;
  const source = typeof value.source === 'string' ? SOURCES[value.source] : undefined;
  if (value.version !== '1' || value.executed !== true ||
      typeof value.executed_at !== 'string' || !Number.isFinite(Date.parse(value.executed_at)) ||
      !source || !object(plan) || plan.version !== '1' || plan.dataset !== source[0] ||
      value.source_grain !== source[1] || !Array.isArray(plan.measures) ||
      plan.measures.length < 1 || plan.measures.length > 3 ||
      !count(plan.limit) || plan.limit < 1 || plan.limit > 500 ||
      !Array.isArray(plan.group_by) || plan.group_by.length > 2 ||
      new Set(plan.group_by).size !== plan.group_by.length ||
      !plan.group_by.every((dim) => ['well_id', 'state', 'basin', 'operator'].includes(dim)) ||
      !['none', 'day', 'month', 'year'].includes(plan.time_bucket as string) ||
      !Array.isArray(plan.filters) || plan.filters.length > 4 ||
      (plan.dataset !== 'wells' &&
        (!date(plan.start_date) || !date(plan.end_date) || plan.start_date > plan.end_date ||
          Date.parse(plan.end_date) - Date.parse(plan.start_date) > 3660 * 86400_000)) ||
      (plan.dataset === 'wells' &&
        (plan.start_date !== null || plan.end_date !== null || plan.time_bucket !== 'none')) ||
      !object(value.units) || !Array.isArray(value.items) || value.items.length > plan.limit ||
      typeof value.truncated !== 'boolean' ||
      !['ok', 'empty', 'truncated'].includes(value.status as string) ||
      (value.status === 'truncated') !== value.truncated ||
      (value.status === 'empty' && value.items.length !== 0) ||
      (value.status === 'ok' && value.items.length === 0) ||
      !Array.isArray(value.joined_sources) ||
      !value.joined_sources.every((name) => name === 'oge_synthetic.wells') ||
      !Array.isArray(value.notes) || !value.notes.every((note) => typeof note === 'string')) return fail();

  const units = value.units;
  const measures = plan.measures.map((measure) => {
    if (!object(measure) || typeof measure.field !== 'string' ||
        typeof measure.aggregation !== 'string') return fail();
    const metric = METRICS[measure.field];
    if (!metric || metric.dataset !== plan.dataset ||
        !metric.aggregations.includes(measure.aggregation)) return fail();
    const key = `${measure.field}_${measure.aggregation}`;
    if (units[key] !== metric.unit) return fail();
    return { key, wells: measure.field === 'wells' };
  });
  if (new Set(measures.map(({ key }) => key)).size !== measures.length) return fail();
  if (Object.keys(value.units).length !== measures.length) return fail();
  let hasNulls = false;
  for (const row of value.items) {
    if (!object(row) || !count(row.source_records) || row.source_records < 1 ||
        !plan.group_by.every((dim) => row[dim] === null || typeof row[dim] === 'string') ||
        (plan.time_bucket !== 'none' && !date(row.period))) return fail();
    for (const key of ['first_observation', 'last_observation']) {
      if (value.source_grain === 'year' ? !count(row[key]) || row[key] < 1 || row[key] > 9999 :
          !(date(row[key]) || (plan.dataset === 'wells' && row[key] === null))) return fail();
    }
    for (const { key, wells } of measures) {
      if (wells) {
        if (!count(row[key]) || row[key] !== row.source_records) return fail();
      } else {
        const nulls = row[`${key}_null_records`];
        if (!count(nulls) || nulls > row.source_records ||
            (nulls === row.source_records ? row[key] !== null :
              typeof row[key] !== 'string' || !/^-?\d+(?:\.\d+)?$/.test(row[key] as string))) return fail();
        hasNulls ||= nulls > 0;
      }
    }
  }
  return { empty: value.items.length === 0, truncated: value.truncated, hasNulls };
}

export function groundedReply(text: unknown, analyses: ReturnType<typeof validateAnalysis>[]) {
  if (typeof text !== 'string' || !text.trim()) throw new AppError(502, 'EMPTY_REPLY');
  if (text.length > 16_000) return fail();
  let value: unknown;
  try { value = JSON.parse(text); } catch { return fail(); }
  if (!object(value)) return fail();
  const keys = Object.keys(value).sort().join(',');
  if (value.kind === 'clarification' || value.kind === 'unsupported') {
    if (keys !== 'kind,reason' || typeof value.reason !== 'string') return fail();
    const templates = NON_DATA[value.kind];
    if (!Object.hasOwn(templates, value.reason)) return fail();
    return { reply: templates[value.reason as keyof typeof templates], truncated: false };
  }
  if (value.kind !== 'answer' || keys !== 'kind,reply' ||
      typeof value.reply !== 'string' || !value.reply.trim() || analyses.length === 0) return fail();
  // Absent data cannot imply zero; partial/null data must carry server-owned caveats.
  const truncated = analyses.some((analysis) => analysis.truncated);
  if (analyses.some((analysis) => analysis.empty)) {
    return {
      reply: truncated
        ? 'The executed analysis was truncated with no usable observations. No total or zero value can be inferred.'
        : 'The executed analysis returned no observations. No total or zero value can be inferred.',
      truncated,
    };
  }
  const caveats = [
    ...(truncated ? ['Partial/truncated executed result: returned groups are not the complete population or an overall total.'] : []),
    ...(analyses.some((analysis) => analysis.hasNulls)
      ? ['Some measure observations are null (unknown, not zero); available aggregates do not establish a complete total.'] : []),
  ];
  const reply = [...caveats, value.reply.trim()].join('\n\n');
  if (reply.length > 16_000) return fail();
  return { reply, truncated };
}
