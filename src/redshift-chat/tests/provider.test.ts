import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { Config } from '../server/config.js';
import { readConfig } from '../server/config.js';
import { AppError, LIMITS } from '../server/contracts.js';
import { parseToolOutput, validateAnalysis } from '../server/grounding.js';
import { agentPayload, createAgent, createResponseCaller, type ResponseCaller } from '../server/providers.js';
import { analysisValue, contextValue, foundryOutput } from './fixtures/foundry.js';

const config: Config = {
  production: true, port: 8080, publicOrigin: 'https://chat.example',
  projectEndpoint: 'https://example.services.ai.azure.com/api/projects/example',
  agentName: 'redshift-chat-agent', agentVersion: '3', mcpUrl: 'https://mcp.example/mcp',
};
const success = (extra: Record<string, unknown> = {}) => ({
  id: 'response-secret', output_text: JSON.stringify({ kind: 'clarification', reason: 'missing_period' }),
  status: 'completed', output: [], incomplete_details: null,
  ...extra,
}) as Awaited<ReturnType<ResponseCaller>>;
const analysisOutput = JSON.stringify(analysisValue);
const contextOutput = JSON.stringify(contextValue);
const answer = (reply = 'For 2025: 123.45 bbl.') => JSON.stringify({ kind: 'answer', reply });
const analysisCall = (output: unknown = analysisOutput, extra = {}) => ({
  type: 'mcp_call', name: 'analyze_data', status: 'completed', output, error: null, ...extra,
});

test('registered-agent SDK shape has fixed budgets, no model, no preview, and server continuation', async () => {
  const controller = new AbortController();
  const input = { message: 'List schemas', previousResponseId: 'server-owned-id', signal: controller.signal };
  const payload = agentPayload(config, input);
  assert.deepEqual(payload.request, {
    input: 'List schemas', previous_response_id: 'server-owned-id',
    max_output_tokens: 800, max_tool_calls: 4, stream: false, store: true,
  });
  assert.deepEqual(payload.options.body, {
    agent_reference: { name: 'redshift-chat-agent', type: 'agent_reference', version: '3' },
  });
  assert.equal(payload.options.maxRetries, 0);
  assert.equal(payload.options.timeout, 230_000);
  assert.equal(payload.options.signal, controller.signal);
  assert.equal('model' in payload.request, false);
  const agent = createAgent(config, async (sent) => {
    assert.deepEqual(sent.request, payload.request);
    return success();
  });
  assert.deepEqual(await agent(input), {
    id: 'response-secret', reply: 'Which inclusive date range should I analyze?', truncated: false, toolNames: [],
  });
});

test('bounded official-MCP deadlines fit four tools and stay below ACA ingress', () => {
  assert.ok(LIMITS.toolCalls * 50_000 < LIMITS.chatTimeoutMs);
  assert.ok(50_000 < LIMITS.healthTimeoutMs);
  assert.ok(LIMITS.chatTimeoutMs < LIMITS.browserTimeoutMs);
  assert.ok(LIMITS.browserTimeoutMs < 240_000);
});

test('agent version is optional; continuation is absent on the first turn', () => {
  const payload = agentPayload({ ...config, agentVersion: undefined }, { message: 'hello', signal: AbortSignal.timeout(100) });
  assert.equal('previous_response_id' in payload.request, false);
  assert.equal('version' in payload.options.body.agent_reference, false);
});

test('tool evidence contains only actual MCP call names, preserving order and repeated calls', async () => {
  const agent = createAgent(config, async () => success({
    output_text: answer('I mention metadata, but did not call it.'),
    output: [
      { type: 'mcp_list_tools', tools: [{ name: 'describe_table' }] },
      { type: 'message', content: [{ type: 'output_text', text: 'test_connection' }] },
      { type: 'mcp_call', name: 'get_data_context', arguments: '{"private":"arguments"}',
        output: contextOutput, id: 'private-call-id', server_label: 'private-server', error: null },
      { type: 'mcp_call', name: 'analyze_data', output: analysisOutput, error: null },
      { type: 'mcp_call', name: 'analyze_data', output: analysisOutput, error: null },
    ],
  }));
  const result = await agent({ message: 'hello', signal: AbortSignal.timeout(100) });
  assert.deepEqual(result.toolNames, ['get_data_context', 'analyze_data', 'analyze_data']);
  assert.deepEqual(Object.keys(result).sort(), ['id', 'reply', 'toolNames', 'truncated']);
  assert.doesNotMatch(JSON.stringify(result.toolNames), /private|describe_table|test_connection/);
});

for (const status of [401, 403, 400, 429, 500, '401', '403', undefined]) {
  test(`provider status ${JSON.stringify(status)} has only the expected safe authorization diagnostic`, async (t) => {
    const log = t.mock.method(console, 'error', () => {});
    let calls = 0;
    const agent = createAgent(config, async () => {
      calls++;
      throw Object.assign(new Error('sensitive downstream body private prompt SECRET'), {
        status, body: 'private tool output', request: { token: 'SECRET', cookie: 'private cookie' },
        providerId: 'private-provider-id',
      });
    });
    await assert.rejects(() => agent({ message: 'private', signal: AbortSignal.timeout(100) }), (error: unknown) => {
      assert.equal((error as AppError).status, 503);
      assert.equal((error as { code: string }).code, status === 401 || status === 403 ? 'AGENT_FORBIDDEN' : 'AGENT_UNAVAILABLE');
      assert.doesNotMatch((error as Error).message, /sensitive|private/);
      return true;
    });
    assert.equal(calls, 1);
    const output = log.mock.calls.map((call) => call.arguments);
    assert.deepEqual(output, status === 401 || status === 403
      ? [[JSON.stringify({ event: 'agent_authorization_failed', upstreamStatus: status })]]
      : []);
    assert.doesNotMatch(JSON.stringify(output), /sensitive|private|SECRET|Error|stack|token|cookie/);
  });
}

test('existing application errors pass through unchanged without an authorization diagnostic', async (t) => {
  const log = t.mock.method(console, 'error', () => {});
  for (const status of [401, 403, 503]) {
    const original = new AppError(status, 'AGENT_FORBIDDEN');
    const agent = createAgent(config, async () => { throw original; });
    await assert.rejects(() => agent({ message: 'private', signal: AbortSignal.timeout(100) }),
      (error: unknown) => error === original);
  }
  assert.equal(log.mock.callCount(), 0);
});

test('empty/noncompleted/unknown-tool/approval-required output never becomes a successful answer', async () => {
  const fixtures = [
    success({ output_text: '' }), success({ status: 'failed' }),
    success({ output: [{ type: 'mcp_call', name: 'execute_sql', error: null }] }),
    success({ output: [{ type: 'mcp_call', name: 'list_schemas', error: { message: 'private database failure' } }] }),
    success({ output: [{ type: 'mcp_approval_request', name: 'list_schemas' }] }),
    success({ output: Array.from({ length: 5 }, () => ({ type: 'mcp_call', name: 'test_connection' })) }),
  ];
  for (const result of fixtures) {
    const agent = createAgent(config, async () => result);
    await assert.rejects(() => agent({ message: 'hello', signal: AbortSignal.timeout(100) }));
  }
});

test('actual official SDK serializes the GA project URL and agent_reference body without a model', async (t) => {
  let requests = 0;
  let tokenRequests = 0;
  const controller = new AbortController();
  const fetchMock = t.mock.method(globalThis, 'fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    requests++;
    assert.equal(String(input), `${config.projectEndpoint}/openai/v1/responses`);
    const body = JSON.parse(init!.body as string);
    assert.equal(body.agent_reference.name, 'redshift-chat-agent');
    assert.equal(body.agent_reference.type, 'agent_reference');
    assert.equal(body.agent_reference.version, '3');
    assert.equal(body.previous_response_id, 'owned-by-server');
    assert.equal(body.max_tool_calls, 4);
    assert.equal(body.max_output_tokens, 800);
    assert.equal('model' in body, false);
    return Response.json({
      id: 'SDK-response', object: 'response', status: 'completed', output: [{
        id: 'message-1', type: 'message', role: 'assistant', status: 'completed',
        content: [{ type: 'output_text', text: JSON.stringify({
          kind: 'unsupported', reason: 'unsupported_scope',
        }), annotations: [] }],
      }],
    });
  });
  const caller = createResponseCaller(config, {
    getToken: async (scopes, options) => {
      tokenRequests++;
      assert.deepEqual(scopes, ['https://ai.azure.com/.default']);
      assert.equal(options?.abortSignal, controller.signal);
      return { token: 'unit-test-not-a-credential', expiresOnTimestamp: Date.now() + 60_000 };
    },
  });
  const agent = createAgent(config, caller);
  assert.equal((await agent({
    message: 'Is Redshift connected?', previousResponseId: 'owned-by-server', signal: controller.signal,
  })).reply, 'That request is outside the supported synthetic analytics scope. Please ask about production, wells, or monthly prices.');
  assert.equal(requests, 1);
  assert.equal(tokenRequests, 1);
  fetchMock.mock.restore();
});

test('incomplete model output fails closed even with execution and parseable JSON', async () => {
  const agent = createAgent(config, async () => success({
    output_text: answer('<script>not executable</script>'),
    status: 'incomplete', incomplete_details: { reason: 'max_output_tokens' },
    output: [{ type: 'mcp_call', name: 'analyze_data', output: analysisOutput, error: null }],
  }));
  await assert.rejects(() => agent({ message: 'hello', signal: AbortSignal.timeout(100) }));
});

test('analytics rejects metadata tools, embedded errors, fabricated execution and raw payloads', async () => {
  for (const output of [
    undefined, 'private raw results', JSON.stringify({ isError: true }),
    JSON.stringify({ version: '1', executed: false }),
    analysisOutput.replace('"oge_synthetic.daily_production"', '"other.secret"'),
    analysisOutput.replace('"executed":true', '"executed":false'),
    'x'.repeat(256 * 1024 + 1),
  ]) {
    const agent = createAgent(config, async () => success({
      output: [{ type: 'mcp_call', name: 'analyze_data', output, error: null }],
    }));
    await assert.rejects(() => agent({ message: 'Total oil?', signal: AbortSignal.timeout(100) }));
  }
  for (const envelope of [
    { structuredContent: JSON.parse(analysisOutput), content: [{ type: 'text', text: analysisOutput }], isError: false },
    { content: [{ type: 'text', text: analysisOutput }] },
  ]) {
    const agent = createAgent(config, async () => success({
      output_text: answer(),
      output: [{ type: 'mcp_call', name: 'analyze_data', output: JSON.stringify(envelope), error: null }],
    }));
    assert.deepEqual((await agent({ message: 'Total oil?', signal: AbortSignal.timeout(100) })).toolNames,
      ['analyze_data']);
  }
});

test('observed two-document fixtures normalize identically to single JSON and official MCP envelopes', () => {
  for (const value of [contextValue, analysisValue]) {
    const paired = foundryOutput(value);
    assert.throws(() => JSON.parse(paired), SyntaxError);
    const direct = parseToolOutput(JSON.stringify(value));
    assert.deepEqual(parseToolOutput(`${JSON.stringify(value)}\n`), direct);
    assert.deepEqual(parseToolOutput(paired), direct);
    assert.deepEqual(parseToolOutput(JSON.stringify({
      content: [{ type: 'text', text: JSON.stringify(value) }], structuredContent: value,
    })), direct);
    if ('executed' in value) {
      assert.deepEqual(validateAnalysis(parseToolOutput(paired)), validateAnalysis(direct));
    }
  }
});

test('two-document boundaries handle multiline objects, quoted delimiters, escapes and reordered keys', () => {
  const value = {
    ...analysisValue,
    notes: ['Braces { } [ ] and "quotes"; slash \\; newline\nnext\tline\rreturn', '\\\\"}\\'],
  };
  const reordered = {
    ...Object.fromEntries(Object.entries(value).reverse()),
    plan: Object.fromEntries(Object.entries(value.plan).reverse()),
    items: value.items.map((row) => Object.fromEntries(Object.entries(row).reverse())),
  };
  const output = ` \t\r\n${JSON.stringify(value, null, 2)}\r\n \t${JSON.stringify({
    structuredResponse: reordered,
  }, null, 2)}\n`;
  assert.deepEqual(parseToolOutput(output), value);
  assert.deepEqual(validateAnalysis(parseToolOutput(output)), validateAnalysis(value));
});

test('official SDK accepts observed GA context plus analysis on first turn and fresh continuation only', async (t) => {
  let requests = 0;
  t.mock.method(globalThis, 'fetch', async (_input: RequestInfo | URL, init?: RequestInit) => {
    requests++;
    const body = JSON.parse(init!.body as string);
    assert.equal(body.previous_response_id, requests === 1 ? undefined : `synthetic-response-${requests - 1}`);
    const output = [
      { type: 'mcp_call', id: 'synthetic-context', server_label: 'synthetic-mcp',
        name: 'get_data_context', arguments: '{}', status: 'completed', error: null,
        output: foundryOutput(contextValue) },
      ...(requests === 3 ? [] : [{
        ...analysisCall(foundryOutput(analysisValue)), id: 'synthetic-analysis',
        server_label: 'synthetic-mcp', arguments: '{}',
      }]),
      { type: 'message', id: 'synthetic-message', role: 'assistant', status: 'completed',
        content: [{ type: 'output_text', text: answer(), annotations: [] }] },
    ];
    return Response.json({
      id: `synthetic-response-${requests}`, object: 'response', status: 'completed', output,
    });
  });
  const agent = createAgent(config, createResponseCaller(config, {
    getToken: async () => ({ token: 'unit-test-not-a-credential', expiresOnTimestamp: Date.now() + 60_000 }),
  }));
  const first = await agent({ message: 'Total oil for 2025?', signal: AbortSignal.timeout(1000) });
  const next = await agent({
    message: 'Analyze again', previousResponseId: first.id, signal: AbortSignal.timeout(1000),
  });
  for (const result of [first, next]) {
    assert.equal(result.reply, 'For 2025: 123.45 bbl.');
    assert.equal(result.truncated, false);
    assert.deepEqual(result.toolNames, ['get_data_context', 'analyze_data']);
    assert.deepEqual(Object.keys(result).sort(), ['id', 'reply', 'toolNames', 'truncated']);
  }
  await assert.rejects(() => agent({
    message: 'Analyze again', previousResponseId: next.id, signal: AbortSignal.timeout(1000),
  }), (error: unknown) => error instanceof AppError && error.code === 'AGENT_UNAVAILABLE');
  assert.equal(requests, 3);
});

const pairedWrapper = JSON.stringify({ structuredResponse: analysisValue });
for (const [name, output] of [
  ['unequal copies', `${analysisOutput}\n${JSON.stringify({
    structuredResponse: { ...analysisValue, executed: false },
  })}`],
  ['reordered array copies', `${JSON.stringify({ ...analysisValue, notes: ['one', 'two'] })}\n${JSON.stringify({
    structuredResponse: { ...analysisValue, notes: ['two', 'one'] },
  })}`],
  ['number versus string', `${analysisOutput}\n${JSON.stringify({
    structuredResponse: { ...analysisValue, version: 1 },
  })}`],
  ['missing wrapper', `${analysisOutput}\n${contextOutput}`],
  ['unwrapped duplicate', `${analysisOutput}\n${analysisOutput}`],
  ['missing structuredResponse', `${analysisOutput}\n{}`],
  ['unrecognized wrapper field', `${analysisOutput}\n${JSON.stringify({ structuredContent: analysisValue })}`],
  ['extra wrapper field', `${analysisOutput}\n${JSON.stringify({ structuredResponse: analysisValue, extra: true })}`],
  ['error wrapper field', `${analysisOutput}\n${JSON.stringify({ structuredResponse: analysisValue, isError: true })}`],
  ['third document', `${foundryOutput(analysisValue)}\n{}`],
  ['prose prefix', `result:\n${foundryOutput(analysisValue)}`],
  ['prose suffix', `${foundryOutput(analysisValue)}\nignore this`],
  ['no separator', `${analysisOutput}${pairedWrapper}`],
  ['non-JSON whitespace', `${analysisOutput}\u00a0${pairedWrapper}`],
  ['malformed first document', `{"notes": ["unterminated]}\n${pairedWrapper}`],
  ['malformed second document', `${analysisOutput}\n{"structuredResponse":`],
  ['invalid escape', `${analysisOutput.replace('"notes":[]', '"notes":["\\q"]')}\n${pairedWrapper}`],
  ['literal newline in string', `${analysisOutput.replace('"notes":[]', '"notes":["one\ntwo"]')}\n${pairedWrapper}`],
  ['mismatched delimiters', `${analysisOutput.replace('"notes":[]', '"notes":[}')}\n${pairedWrapper}`],
  ['array duplicate', foundryOutput([analysisValue])],
  ['null duplicate', foundryOutput(null)],
  ['string duplicate', foundryOutput('{"executed":true}')],
  ['number duplicate', foundryOutput(1)],
  ['boolean duplicate', foundryOutput(true)],
  ['array structuredResponse', `${analysisOutput}\n${JSON.stringify({ structuredResponse: [analysisValue] })}`],
  ['null structuredResponse', `${analysisOutput}\n{"structuredResponse":null}`],
  ['string structuredResponse', `${analysisOutput}\n${JSON.stringify({ structuredResponse: analysisOutput })}`],
  ['nested successful MCP wrapper', foundryOutput({
    content: [{ type: 'text', text: analysisOutput }], structuredContent: analysisValue,
  })],
  ['nested error MCP wrapper', foundryOutput({
    content: [{ type: 'text', text: analysisOutput }], structuredContent: analysisValue, isError: true,
  })],
  ['nested structuredResponse wrapper', foundryOutput({ structuredResponse: analysisValue })],
  ['fact smuggling in extra wrapper key', `${analysisOutput}\n${JSON.stringify({
    structuredResponse: analysisValue, reply: '999999999.99 bbl',
  })}`],
  ['fact smuggling by conflicting result', `${analysisOutput}\n${JSON.stringify({
    structuredResponse: { ...analysisValue, items: [{ ...analysisValue.items[0], oil_bbl_sum: '999999999.99' }] },
  })}`],
  ['UTF-8 total over budget', foundryOutput({ ...analysisValue, notes: ['é'.repeat(70_000)] })],
  ['trailing whitespace over budget', `${foundryOutput(analysisValue)}${' '.repeat(256 * 1024)}`],
] as const) {
  test(`two-document output rejects ${name}`, async () => {
    assert.throws(() => parseToolOutput(output),
      (error: unknown) => error instanceof AppError && error.code === 'AGENT_UNAVAILABLE');
    const agent = createAgent(config, async () => success({
      output_text: answer(), output: [analysisCall(output)],
    }));
    await assert.rejects(() => agent({ message: 'Total?', signal: AbortSignal.timeout(100) }),
      (error: unknown) => error instanceof AppError && error.code === 'AGENT_UNAVAILABLE');
  });
}

test('total original UTF-8 size bound includes both documents and surrounding whitespace', () => {
  const paired = foundryOutput(analysisValue);
  const atLimit = paired + ' '.repeat(256 * 1024 - Buffer.byteLength(paired, 'utf8'));
  assert.deepEqual(parseToolOutput(atLimit), analysisValue);
  assert.throws(() => parseToolOutput(atLimit + ' '), AppError);
});

test('two-document context normalizes but never grounds an answer or smuggles nondata facts', async () => {
  for (const previousResponseId of [undefined, 'previous-executed-analysis']) {
    for (const output_text of [
      answer('999999999.99 bbl'),
      JSON.stringify({ kind: 'clarification', reason: 'missing_period', reply: '999999999.99 bbl' }),
      JSON.stringify({ kind: 'unsupported', reason: '999999999.99 bbl' }),
    ]) {
      const agent = createAgent(config, async () => success({
        output_text, output: [{ ...analysisCall(foundryOutput(contextValue)), name: 'get_data_context' }],
      }));
      await assert.rejects(() => agent({
        message: 'Total?', previousResponseId, signal: AbortSignal.timeout(100),
      }), AppError);
    }
  }
  const agent = createAgent(config, async () => success({
    output: [{ ...analysisCall(foundryOutput(contextValue)), name: 'get_data_context' }],
  }));
  assert.equal((await agent({ message: 'Total?', signal: AbortSignal.timeout(100) })).reply,
    'Which inclusive date range should I analyze?');
});

test('paired output still rejects failed calls, nested errors and later invalid executions', async () => {
  for (const call of [
    analysisCall(foundryOutput(analysisValue), { status: 'failed' }),
    analysisCall(foundryOutput(analysisValue), { error: { message: 'synthetic failure' } }),
    analysisCall(foundryOutput({ ...analysisValue, isError: true })),
    analysisCall(foundryOutput(contextValue)),
    { ...analysisCall(foundryOutput(analysisValue)), name: 'get_data_context' },
    analysisCall(JSON.stringify({
      content: [{ type: 'text', text: foundryOutput(analysisValue) }], structuredContent: analysisValue,
    })),
  ]) {
    const agent = createAgent(config, async () => success({
      output_text: answer(), output: [analysisCall(foundryOutput(analysisValue)), call],
    }));
    await assert.rejects(() => agent({ message: 'Total?', signal: AbortSignal.timeout(100) }),
      (error: unknown) => error instanceof AppError && error.code === 'AGENT_UNAVAILABLE');
  }
});

for (const continuation of [false, true]) {
  for (const contextOnly of [false, true]) {
    test(`fake total without current analysis rejects: continuation=${continuation}, context=${contextOnly}`, async () => {
      for (const output_text of [
        'Total oil production in 2025 was 999999999.99 bbl.',
        answer('Total oil production in 2025 was 999999999.99 bbl.'),
      ]) {
        const agent = createAgent(config, async () => success({
          output_text, output: contextOnly ? [{
            type: 'mcp_call', name: 'get_data_context', output: contextOutput, error: null,
          }] : [],
        }));
        await assert.rejects(() => agent({
          message: 'What is actual total oil production in 2025?',
          ...(continuation ? { previousResponseId: 'previous-executed-analysis' } : {}),
          signal: AbortSignal.timeout(100),
        }));
      }
    });
  }
}

test('grounded first answer and followup each require their own valid execution', async () => {
  let turn = 0;
  const agent = createAgent(config, async (payload) => {
    turn++;
    assert.equal(payload.request.previous_response_id, turn === 1 ? undefined : 'response-secret');
    return success({ output_text: answer(), output: turn === 1 ? [analysisCall()] : [] });
  });
  const first = await agent({ message: 'Total oil for 2025?', signal: AbortSignal.timeout(100) });
  assert.equal(first.reply, 'For 2025: 123.45 bbl.');
  assert.equal(first.truncated, false);
  await assert.rejects(() => agent({
    message: 'And gas?', previousResponseId: first.id, signal: AbortSignal.timeout(100),
  }));
  const fresh = createAgent(config, async () => success({ output_text: answer(), output: [analysisCall()] }));
  assert.equal((await fresh({
    message: 'Oil again?', previousResponseId: first.id, signal: AbortSignal.timeout(100),
  })).reply, first.reply);
});

test('non-data responses use only server-owned reason templates, never model prose', async () => {
  for (const [kind, reason, reply] of [
    ['clarification', 'missing_period', 'Which inclusive date range should I analyze?'],
    ['clarification', 'ambiguous_request', 'Please specify the metric, period, and any grouping or filters to analyze.'],
    ['unsupported', 'unsupported_metric', 'That calculation is not supported. I can analyze production and operating-cost sums, well counts, or monthly price averages, minima and maxima.'],
    ['unsupported', 'unsupported_scope', 'That request is outside the supported synthetic analytics scope. Please ask about production, wells, or monthly prices.'],
  ]) {
    const agent = createAgent(config, async () => success({ output_text: JSON.stringify({ kind, reason }) }));
    assert.equal((await agent({ message: 'Help?', signal: AbortSignal.timeout(100) })).reply, reply);
    for (const forged of [
      { kind, reason, reply: '999999999.99 bbl' }, { kind, reason: '999999999.99 bbl' },
      { kind, reason, data: '999999999.99 bbl' },
    ]) {
      const bad = createAgent(config, async () => success({ output_text: JSON.stringify(forged) }));
      await assert.rejects(() => bad({ message: 'Total?', signal: AbortSignal.timeout(100) }));
    }
  }
});

test('strict answer protocol rejects unknown, extra, malformed, oversized and plain text output', async () => {
  for (const output_text of [
    '{}', '[]', 'null', '{"kind":"answer","reply":', '```json\n' + answer() + '\n```',
    answer(''), JSON.stringify({ kind: 'answer', reply: '123.45 bbl', reason: 'missing_period' }),
    JSON.stringify({ kind: 'unknown', reply: '123.45 bbl' }), answer('x'.repeat(16_001)),
  ]) {
    const agent = createAgent(config, async () => success({ output_text, output: [analysisCall()] }));
    await assert.rejects(() => agent({ message: 'Total?', signal: AbortSignal.timeout(100) }));
  }
});

test('failed/incomplete calls and malformed executed result fields cannot ground an answer', async () => {
  const invalid = [
    ...['failed', 'incomplete', 'in_progress', 'calling'].map((status) => analysisCall(analysisOutput, { status })),
    analysisCall(analysisOutput, { error: { message: 'private' } }),
    ...[
      { executed: false }, { status: 'failed' }, { status: 'empty' }, { status: 'truncated' },
      { items: [] }, { units: {} }, { units: { oil_bbl_sum: 'Mcf' } }, { plan: { version: '1' } },
      { executed_at: 'not-a-date' }, { source_grain: 'year' },
      { plan: { ...analysisValue.plan, start_date: 'not-a-date' } },
      { plan: { ...analysisValue.plan, start_date: '2025-02-30' } },
      { source: 'oge_synthetic.monthly_prices' }, { items: [{ oil_bbl_sum: '999.99' }] },
      { items: [{ ...JSON.parse(analysisOutput).items[0], oil_bbl_sum: 'NaN' }] },
      { items: [{ ...JSON.parse(analysisOutput).items[0], first_observation: {} }] },
      { items: [{ ...JSON.parse(analysisOutput).items[0], oil_bbl_sum_null_records: -1 }] },
      { items: [{ ...JSON.parse(analysisOutput).items[0], oil_bbl_sum_null_records: 3 }] },
    ].flatMap((change) => {
      const value = { ...analysisValue, ...change };
      return [analysisCall(JSON.stringify(value)), analysisCall(foundryOutput(value))];
    }),
    ...[
      { isError: true, content: [{ type: 'text', text: analysisOutput }], structuredContent: analysisValue },
      { content: [{ type: 'text', text: '{"isError":true}' }], structuredContent: analysisValue },
      { content: [], structuredContent: analysisValue },
      { content: [{ type: 'text', text: analysisOutput }], structuredContent: [] },
    ].map((envelope) => analysisCall(JSON.stringify(envelope))),
  ];
  for (const call of invalid) {
    const agent = createAgent(config, async () => success({ output_text: answer(), output: [call] }));
    await assert.rejects(() => agent({ message: 'Total?', signal: AbortSignal.timeout(100) }));
  }
});

test('all documented source grains, prices and wells support valid fresh analysis', async () => {
  for (const [source, grain] of [
    ['daily_production', 'day'], ['monthly_production', 'month'], ['annual_production', 'year'],
    ['monthly_prices', 'month'], ['wells', 'well'],
  ]) {
    const value = structuredClone(analysisValue) as Record<string, unknown>;
    value.source = `oge_synthetic.${source}`;
    value.source_grain = grain;
    if (source === 'annual_production') {
      value.items = [{ ...analysisValue.items[0], first_observation: 2025, last_observation: 2025 }];
    } else if (source === 'monthly_prices') {
      value.plan = {
        ...analysisValue.plan, dataset: 'prices',
        measures: [{ field: 'oil_usd_per_bbl', aggregation: 'avg' }],
      };
      value.units = { oil_usd_per_bbl_avg: 'USD/bbl' };
      value.items = [{
        oil_usd_per_bbl_avg: '60.12345678', oil_usd_per_bbl_avg_null_records: 0,
        source_records: 12, first_observation: '2025-01-01', last_observation: '2025-12-01',
      }];
    } else if (source === 'wells') {
      value.plan = {
        ...analysisValue.plan, dataset: 'wells', start_date: null, end_date: null,
        measures: [{ field: 'wells', aggregation: 'count' }],
      };
      value.units = { wells_count: 'wells' };
      value.items = [{
        wells_count: 2, source_records: 2,
        first_observation: '2020-01-01', last_observation: '2020-12-01',
      }];
    }
    const agent = createAgent(config, async () => success({
      output_text: answer('An executed result.'), output: [analysisCall(JSON.stringify(value))],
    }));
    assert.equal((await agent({ message: 'Analyze', signal: AbortSignal.timeout(100) })).reply, 'An executed result.');
  }
});

test('empty results cannot imply zero; valid top-N and null results carry server-owned caveats', async () => {
  for (const [change, expected, truncated] of [
    [{ status: 'empty', items: [] }, /no observations.*No total or zero/i, false],
    [{ status: 'truncated', truncated: true }, /partial\/truncated.*not the complete population/i, true],
    [{ status: 'truncated', truncated: true, items: [] }, /truncated with no usable observations/i, true],
    [{ items: [{
      ...JSON.parse(analysisOutput).items[0], oil_bbl_sum: null, oil_bbl_sum_null_records: 2,
    }] }, /unknown, not zero/, false],
  ] as const) {
    const agent = createAgent(config, async () => success({
      output_text: answer('The returned observations are incomplete.'),
      output: [analysisCall(JSON.stringify({ ...analysisValue, ...change }))],
    }));
    const result = await agent({ message: 'Total?', signal: AbortSignal.timeout(100) });
    assert.match(result.reply, expected);
    assert.equal(result.truncated, truncated);
    if ('items' in change && change.items.length === 0) assert.doesNotMatch(result.reply, /returned observations/);
    else assert.match(result.reply, /returned observations are incomplete/);
    const paired = createAgent(config, async () => success({
      output_text: answer('The returned observations are incomplete.'),
      output: [analysisCall(foundryOutput({ ...analysisValue, ...change }))],
    }));
    assert.deepEqual(await paired({ message: 'Total?', signal: AbortSignal.timeout(100) }), result);
  }
});

test('official SDK 403 is attempted once with no fallback and a sanitized scope failure', async (t) => {
  const log = t.mock.method(console, 'error', () => {});
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => {
    calls++;
    return Response.json({ error: { message: 'SECRET authorization body', code: 'Forbidden' } }, { status: 403 });
  });
  const caller = createResponseCaller(config, {
    getToken: async () => ({ token: 'unit-test-not-a-credential', expiresOnTimestamp: Date.now() + 60_000 }),
  });
  const agent = createAgent(config, caller);
  await assert.rejects(() => agent({ message: 'private', signal: AbortSignal.timeout(1000) }), (error: unknown) => {
    assert.equal((error as { code: string }).code, 'AGENT_FORBIDDEN');
    assert.doesNotMatch((error as Error).message, /SECRET/);
    return true;
  });
  assert.equal(calls, 1);
  assert.deepEqual(log.mock.calls.map((call) => call.arguments), [
    [JSON.stringify({ event: 'agent_authorization_failed', upstreamStatus: 403 })],
  ]);
});

test('official SDK request is cancelled by the dispatch signal with no hidden retry', async (t) => {
  const controller = new AbortController();
  let started!: () => void;
  let wasAborted = false;
  const ready = new Promise<void>((resolve) => { started = resolve; });
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async (_input: RequestInfo | URL, init?: RequestInit) => {
    calls++;
    started();
    return new Promise<Response>((_resolve, reject) => {
      init!.signal!.addEventListener('abort', () => {
        wasAborted = true;
        reject(new DOMException('Aborted', 'AbortError'));
      }, { once: true });
    });
  });
  const caller = createResponseCaller(config, {
    getToken: async () => ({ token: 'unit-test-not-a-credential', expiresOnTimestamp: Date.now() + 60_000 }),
  });
  const work = caller(agentPayload(config, { message: 'hello', signal: controller.signal }));
  await ready;
  controller.abort();
  await assert.rejects(() => work);
  assert.equal(wasAborted, true);
  assert.equal(calls, 1);
});

test('production config requires exact HTTPS origin and secure server-owned endpoints', () => {
  const env = {
    NODE_ENV: 'production', PUBLIC_ORIGIN: config.publicOrigin,
    FOUNDRY_PROJECT_ENDPOINT: config.projectEndpoint, MCP_SERVER_URL: config.mcpUrl,
  };
  assert.equal(readConfig(env).agentName, 'redshift-chat-agent');
  assert.equal(readConfig(env).port, 8080);
  for (const overrides of [
    { PUBLIC_ORIGIN: 'http://example.com' }, { PUBLIC_ORIGIN: 'https://chat.example/' },
    { FOUNDRY_PROJECT_ENDPOINT: 'https://evil.invalid/api/projects/x' },
    { MCP_SERVER_URL: 'https://user:password@example.com/mcp' },
    { MCP_SERVER_URL: 'http://example.com/mcp' }, { PORT: 'not-a-port' },
    { FOUNDRY_AGENT_NAME: 'name/endpoint' }, { FOUNDRY_AGENT_VERSION: 'a b' },
  ]) assert.throws(() => readConfig({ ...env, ...overrides }));
  assert.throws(() => readConfig({}));
  const dev = readConfig({ ...env, NODE_ENV: 'development', PUBLIC_ORIGIN: 'http://127.0.0.1:5173' });
  assert.equal(dev.production, false);
  assert.throws(() => readConfig({ ...env, NODE_ENV: 'development', PUBLIC_ORIGIN: 'http://0.0.0.0:5173' }));
});
