import assert from 'node:assert/strict';
import { once } from 'node:events';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { test, type TestContext } from 'node:test';
import type { AddressInfo } from 'node:net';
import { createApp, clientIp } from '../server/app.js';
import type { Config } from '../server/config.js';
import { AppError, LIMITS, type Agent, type AgentReply, type AgentRequest } from '../server/contracts.js';
import { HealthMonitor } from '../server/health.js';
import { createAgent, type ResponseCaller } from '../server/providers.js';
import { RateLimiter, Sessions } from '../server/state.js';
import { analysisValue, contextValue, foundryOutput } from './fixtures/foundry.js';
import { dataQualityPrompt } from './fixtures/data-quality-prompt.js';

const config: Config = {
  production: true, port: 8080, publicOrigin: 'https://chat.example',
  projectEndpoint: 'https://example.services.ai.azure.com/api/projects/example',
  agentName: 'redshift-chat-agent', mcpUrl: 'https://mcp.example/mcp',
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

async function fixture(t: TestContext, overrides: {
  agent?: Agent; now?: () => number; limiter?: RateLimiter; chatTimeoutMs?: number; maxSessions?: number; config?: Config;
} = {}) {
  const calls: AgentRequest[] = [];
  const logs: string[] = [];
  const app = createApp({
    config: overrides.config ?? config, clientDir: path.resolve('tests/fixtures/client'),
    health: new HealthMonitor(async () => true),
    agent: overrides.agent ?? (async (request) => {
      calls.push(request);
      return { id: `response-${calls.length}`, reply: 'Mocked answer.', truncated: false, toolNames: [] };
    }),
    limiter: overrides.limiter ?? new RateLimiter(overrides.now, 10_000, 1000),
    now: overrides.now, sessions: new Sessions(overrides.now, overrides.maxSessions),
    chatTimeoutMs: overrides.chatTimeoutMs, log: (code) => logs.push(code),
  });
  app.server.listen(0, '127.0.0.1');
  await once(app.server, 'listening');
  t.after(() => app.close());
  const base = `http://127.0.0.1:${(app.server.address() as AddressInfo).port}`;
  const post = async (route: string, body: unknown, cookie?: string, headers: Record<string, string> = {}) =>
    fetch(`${base}${route}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: config.publicOrigin, ...(cookie ? { Cookie: cookie } : {}), ...headers },
      body: JSON.stringify(body),
    });
  const send = (message: string, cookie?: string) => post('/api/chat', { message }, cookie);
  return { ...app, base, post, send, calls, logs };
}
function cookie(response: Response): string {
  return response.headers.get('set-cookie')!.split(';')[0]!;
}

test('chat creates a secure opaque cookie and only server-owned continuation reaches the agent', async (t) => {
  const f = await fixture(t);
  const first = await f.send('What schemas exist?');
  assert.equal(first.status, 200);
  assert.match(first.headers.get('set-cookie')!, /^__Host-redshift-chat=[\w-]{43}; Path=\/; HttpOnly; SameSite=Strict; Max-Age=1800; Secure$/);
  const body = await first.json();
  assert.equal(body.reply, 'Mocked answer.');
  assert.equal(body.turnsRemaining, 19);
  assert.equal(body.truncated, false);
  assert.deepEqual(body.toolNames, []);
  assert.equal(body.continued, false);
  assert.deepEqual(Object.keys(body).sort(), ['continued', 'expiresAt', 'reply', 'toolNames', 'truncated', 'turnsRemaining']);
  assert.ok(Number.isFinite(Date.parse(body.expiresAt)));
});

test('continuation and session isolation never expose provider identifiers', async (t) => {
  const f = await fixture(t);
  const first = await f.send('List schemas');
  const data = await first.json();
  assert.equal(data.turnsRemaining, 19);
  assert.equal(data.reply, 'Mocked answer.');
  assert.equal(data.continued, false);
  assert.equal('id' in data, false);
  assert.equal('previous_response_id' in data, false);
  const second = await f.send('And tables?', cookie(first));
  assert.equal(second.status, 200);
  const continuation = await second.json();
  assert.equal(continuation.turnsRemaining, 18);
  assert.equal(continuation.continued, true);
  assert.equal(f.calls[0]!.previousResponseId, undefined);
  assert.equal(f.calls[1]!.previousResponseId, 'response-1');
  const isolated = await f.send('Fresh chain');
  assert.notEqual(cookie(isolated), cookie(first));
  assert.equal(f.calls[2]!.previousResponseId, undefined);
  assert.equal((await isolated.json()).continued, false);
});

test('HTTP evidence comes from provider MCP calls only and omits private tool fields and response IDs', async (t) => {
  const f = await fixture(t, { agent: createAgent(config, async () => ({
    id: 'private-response-id', status: 'completed', incomplete_details: null,
    output_text: JSON.stringify({ kind: 'clarification', reason: 'missing_period' }),
    output: [
      { type: 'mcp_list_tools', tools: [{ name: 'describe_table' }] },
      { type: 'mcp_call', name: 'get_data_context', arguments: 'private-arguments',
        output: JSON.stringify({ version: '1', schema: 'oge_synthetic', datasets: {} }),
        id: 'private-call-id', error: null },
    ],
  }) as Awaited<ReturnType<ResponseCaller>>) });
  const first = await f.send('Total oil?');
  const raw = await first.text();
  const body = JSON.parse(raw);
  assert.equal(first.status, 200);
  assert.equal(body.reply, 'Which inclusive date range should I analyze?');
  assert.deepEqual(body.toolNames, ['get_data_context']);
  assert.equal(body.continued, false);
  assert.doesNotMatch(raw, /private-|arguments|output|describe_table|response_id/);
  const next = await f.send('And gas?', cookie(first));
  assert.equal((await next.json()).continued, true);
});

test('HTTP rejects an unexecuted claimed total without leaking model text or provider data', async (t) => {
  const f = await fixture(t, { agent: createAgent(config, async () => ({
    id: 'private-response-id', status: 'completed', incomplete_details: null,
    output_text: JSON.stringify({ kind: 'answer', reply: '999999999.99 bbl in 2025' }),
    output: [],
  }) as Awaited<ReturnType<ResponseCaller>>) });
  const response = await f.send('Actual oil production in 2025?');
  assert.equal(response.status, 503);
  const raw = await response.text();
  assert.equal(JSON.parse(raw).error.code, 'AGENT_INVALID_RESPONSE');
  assert.doesNotMatch(raw, /999999999|private-|toolNames|reply/);
});

test('the full data-quality prompt returns the actual grouping rejection, consumes one turn and logs only its safe code', async (t) => {
  let calls = 0;
  const f = await fixture(t, { agent: createAgent(config, async (payload) => {
    calls++;
    assert.equal(payload.request.previous_response_id, undefined);
    if (calls === 1) {
      assert.equal(payload.request.input, dataQualityPrompt);
      throw Object.assign(new Error('1 validation error for analyze_data\nplan.group_by\n' +
        ' List should have at most 2 items after validation, not 4 [type=too_long, input_value=SECRET]'), {
        status: 400, code: 'tool_user_error', error: { code: 'tool_user_error' }, responseId: 'private-id',
      });
    }
    return {
      id: 'private-id', status: 'completed', incomplete_details: null, output: [],
      output_text: '{"kind":"clarification","reason":"missing_period"}',
    } as Awaited<ReturnType<ResponseCaller>>;
  }) });
  const first = await f.send(dataQualityPrompt);
  assert.equal(first.status, 503);
  const raw = await first.text();
  const body = JSON.parse(raw);
  assert.equal(body.error.code, 'ANALYSIS_GROUP_LIMIT');
  assert.match(body.error.message, /at most two/);
  assert.equal(body.turnsRemaining, 19);
  assert.equal(calls, 1);
  assert.deepEqual(f.logs, ['ANALYSIS_GROUP_LIMIT']);
  assert.doesNotMatch(raw, /SECRET|private-id|input_value|tool_user_error|toolNames|"reply"/);
  const next = await f.send('A smaller question', cookie(first));
  assert.equal(next.status, 200);
  assert.equal((await next.json()).continued, false);
  assert.equal(calls, 2);
});

test('HTTP observed GA encoding preserves public shape and requires fresh same-cookie analysis', async (t) => {
  let calls = 0;
  const f = await fixture(t, { agent: createAgent(config, async (payload) => {
    calls++;
    assert.equal(payload.request.previous_response_id, calls === 1 ? undefined : `synthetic-response-${calls - 1}`);
    return {
      id: `synthetic-response-${calls}`, status: 'completed', incomplete_details: null,
      output_text: JSON.stringify({ kind: 'answer', reply: 'For 2025: 123.45 bbl.' }),
      output: [
        { type: 'mcp_call', name: 'get_data_context', output: foundryOutput(contextValue), error: null },
        ...(calls === 3 ? [] : [{
          type: 'mcp_call', name: 'analyze_data', output: foundryOutput(analysisValue), error: null,
        }]),
      ],
    } as Awaited<ReturnType<ResponseCaller>>;
  }) });
  const first = await f.send('Total oil for 2025?');
  const token = cookie(first);
  const next = await f.send('Analyze again', token);
  for (const [response, continued] of [[first, false], [next, true]] as const) {
    assert.equal(response.status, 200);
    const raw = await response.text();
    const value = JSON.parse(raw);
    assert.equal(value.reply, 'For 2025: 123.45 bbl.');
    assert.equal(value.continued, continued);
    assert.equal(value.truncated, false);
    assert.deepEqual(value.toolNames, ['get_data_context', 'analyze_data']);
    assert.deepEqual(Object.keys(value).sort(),
      ['continued', 'expiresAt', 'reply', 'toolNames', 'truncated', 'turnsRemaining']);
    assert.doesNotMatch(raw, /synthetic-response|structuredResponse|executed|source_records/);
  }
  const ungrounded = await f.send('Analyze again', token);
  assert.equal(ungrounded.status, 503);
  const raw = await ungrounded.text();
  assert.equal(JSON.parse(raw).error.code, 'AGENT_INVALID_RESPONSE');
  assert.doesNotMatch(raw, /123\.45|synthetic-response|structuredResponse|reply|toolNames/);
});

test('turn 21 is rejected before any provider call; failures and retries consume turns', async (t) => {
  const f = await fixture(t);
  const first = await f.send('hello');
  const token = cookie(first);
  for (let turn = 2; turn <= 20; turn++) {
    const response = await f.send(`Turn ${turn}`, token);
    assert.equal(response.status, 200);
    assert.equal((await response.json()).turnsRemaining, 20 - turn);
  }
  const blocked = await f.send('One more', token);
  assert.equal(blocked.status, 409);
  assert.equal((await blocked.json()).error.code, 'TURN_LIMIT');
  assert.equal(f.calls.length, 20);
});

test('reset creates a new chain; expired/unknown cookies never silently create another', async (t) => {
  let time = 1_000_000;
  const f = await fixture(t, { now: () => time });
  const first = await f.send('hello');
  const old = cookie(first);
  time += LIMITS.sessionTtlMs;
  const expired = await f.send('follow up', old);
  assert.equal(expired.status, 409);
  assert.equal((await expired.json()).error.code, 'SESSION_EXPIRED');
  assert.equal(expired.headers.get('set-cookie'), null);
  const reset = await f.post('/api/session/reset', {}, old);
  assert.equal(reset.status, 200);
  assert.notEqual(cookie(reset), old);
  const fresh = await f.send('new question', cookie(reset));
  assert.equal(fresh.status, 200);
  assert.equal((await fresh.json()).continued, false);
  assert.equal(f.calls[1]!.previousResponseId, undefined);
  assert.equal((await f.send('forged', `__Host-redshift-chat=${'a'.repeat(43)}`)).status, 409);
  const duplicate = `${cookie(reset)}; ${cookie(reset)}`;
  assert.equal((await f.send('duplicate', duplicate)).status, 409);
  assert.equal((await f.post('/api/session/reset', {}, '__Host-redshift-chat=bad')).status, 200);
});

test('CSRF, JSON-only, unexpected fields, input bounds and unknown routes fail closed', async (t) => {
  const f = await fixture(t);
  for (const body of [
    { message: 'hi', previous_response_id: 'foreign' }, { message: 'hi', model: 'other' },
    { message: 'hi', agent: 'other' }, { message: 'hi', mcpUrl: 'https://evil.invalid' },
    { message: 'x'.repeat(LIMITS.inputCharacters + 1) }, { message: ' ' }, { message: 42 }, [], null,
  ]) assert.equal((await f.post('/api/chat', body)).status, 400);
  assert.equal((await f.post('/api/chat', { message: 'hi' }, undefined, { Origin: 'https://evil.invalid' })).status, 403);
  const noOrigin = await fetch(`${f.base}/api/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"message":"hi"}',
  });
  assert.equal(noOrigin.status, 403);
  assert.equal((await f.post('/api/chat', { message: 'hi' }, undefined, { 'Content-Type': 'text/plain' })).status, 415);
  assert.equal((await f.post('/api/session/reset', { session: 'foreign' })).status, 400);
  const malformed = await fetch(`${f.base}/api/chat`, {
    method: 'POST', headers: { Origin: config.publicOrigin, 'Content-Type': 'application/json' }, body: '{',
  });
  assert.equal(malformed.status, 400);
  assert.equal((await f.post('/api/chat', { message: 'x'.repeat(LIMITS.requestBytes) })).status, 413);
  assert.equal((await fetch(`${f.base}/api/health?url=https://evil.invalid`)).status, 400);
  assert.equal((await f.post('/api/query', { sql: 'select' })).status, 404);
  assert.equal((await fetch(`${f.base}/api/config`, { headers: { 'Sec-Fetch-Site': 'cross-site' } })).status, 403);
  assert.equal(f.calls.length, 0);
});

test('the full data-quality prompt reaches the agent without truncation', async (t) => {
  const f = await fixture(t);
  assert.ok(dataQualityPrompt.length > 2000 && dataQualityPrompt.length <= LIMITS.inputCharacters);
  assert.equal((await f.send(dataQualityPrompt)).status, 200);
  assert.equal(f.calls[0]!.message, dataQualityPrompt);
  assert.ok(f.calls[0]!.message.endsWith('3. Run the monthly price/revenue check as well? (Y/N)'));
});

test('input character and JSON byte budgets agree at the exact boundary', async (t) => {
  const f = await fixture(t);
  for (const message of ['x'.repeat(LIMITS.inputCharacters), '\uD800'.repeat(LIMITS.inputCharacters)]) {
    assert.ok(Buffer.byteLength(JSON.stringify({ message })) <= LIMITS.requestBytes);
    assert.equal((await f.send(message)).status, 200);
    assert.equal(f.calls.at(-1)!.message, message);
  }
  const tooLong = await f.send('x'.repeat(LIMITS.inputCharacters + 1));
  assert.equal(tooLong.status, 400);
  assert.match((await tooLong.json()).error.message, /32,000/);
  assert.equal(f.calls.length, 2);
});

test('per-session lock is atomic, reset cannot race a provider call, and global concurrency is two', async (t) => {
  const gate = deferred<AgentReply>();
  const started = deferred<void>();
  let calls = 0;
  const f = await fixture(t, { agent: async () => { calls++; started.resolve(); return gate.promise; } });
  const reset = await f.post('/api/session/reset', {});
  const token = cookie(reset);
  const first = f.send('first', token);
  await started.promise;
  assert.equal((await f.send('racing', token)).status, 409);
  assert.equal((await f.post('/api/session/reset', {}, token)).status, 409);
  const second = f.send('second independent');
  while (calls < 2) await sleep(1);
  assert.equal((await f.send('third independent')).status, 503);
  assert.equal(calls, 2);
  gate.resolve({ id: 'done', reply: 'Answer', truncated: false, toolNames: [] });
  assert.equal((await first).status, 200);
  assert.equal((await second).status, 200);
  const resumed = await f.send('next', token);
  assert.equal((await resumed.json()).turnsRemaining, 18);
});

test('timeout cancels the SDK; locks survive uncooperative work and chain requires explicit reset', async (t) => {
  const gate = deferred<AgentReply>();
  let signal: AbortSignal | undefined;
  const f = await fixture(t, { chatTimeoutMs: 15, agent: async (request) => { signal = request.signal; return gate.promise; } });
  const timedOut = await f.send('question');
  const token = cookie(timedOut);
  assert.equal(timedOut.status, 504);
  assert.equal(signal?.aborted, true);
  assert.equal((await timedOut.json()).turnsRemaining, 19);
  assert.equal((await f.send('while hanging', token)).status, 409);
  assert.equal((await f.post('/api/session/reset', {}, token)).status, 409);
  gate.resolve({ id: 'late-response', reply: 'Late', truncated: false, toolNames: [] });
  await sleep(5);
  const uncertain = await f.send('after late answer', token);
  assert.equal((await uncertain.json()).error.code, 'CHAT_TIMEOUT');
  assert.equal((await f.post('/api/session/reset', {}, token)).status, 200);
});

test('managed-identity scope failure is actionable and sanitized, with attempts charged', async (t) => {
  let calls = 0;
  const f = await fixture(t, { agent: async () => { calls++; throw new AppError(503, 'AGENT_FORBIDDEN'); } });
  const first = await f.send('private prompt');
  const body = await first.json();
  assert.equal(first.status, 503);
  assert.equal(body.error.code, 'AGENT_FORBIDDEN');
  assert.match(body.error.message, /managed-identity project access/);
  assert.equal(body.turnsRemaining, 19);
  const retry = await f.send('private prompt', cookie(first));
  assert.equal((await retry.json()).turnsRemaining, 18);
  assert.equal(calls, 2);
  assert.deepEqual(f.logs, ['AGENT_FORBIDDEN', 'AGENT_FORBIDDEN']);
});

test('unexpected downstream errors never appear in JSON or logs', async (t) => {
  const f = await fixture(t, { agent: async () => { throw new Error('SECRET token=abc prompt=private'); } });
  const response = await f.send('private');
  assert.equal(response.status, 500);
  assert.doesNotMatch(await response.text(), /SECRET|token|private/);
  assert.deepEqual(f.logs, ['INTERNAL']);
});

test('socket fallback rejects spoofed forwarding and dynamic routes share a bounded 5/minute limit', async (t) => {
  let time = 1_000_000;
  const f = await fixture(t, { now: () => time, limiter: new RateLimiter(() => time) });
  for (let i = 0; i < 5; i++) {
    const response = await fetch(`${f.base}/api/config`, { headers: { 'X-Forwarded-For': `192.0.2.${i}`, 'X-Real-IP': `192.0.2.${i}` } });
    assert.equal(response.status, 200);
  }
  for (const route of ['/api/health', '/api/config']) {
    const response = await fetch(`${f.base}${route}`, { headers: { 'X-Forwarded-For': '198.51.100.1' } });
    assert.equal(response.status, 429);
    assert.equal(response.headers.get('retry-after'), '60');
  }
  assert.equal((await f.post('/api/session/reset', {})).status, 429);
  assert.equal((await f.send('hi')).status, 429);
  assert.equal((await fetch(`${f.base}/healthz`)).status, 200);
  time += 60_000;
  assert.equal((await fetch(`${f.base}/api/config`)).status, 200);
  assert.equal(clientIp({ socket: { remoteAddress: '::ffff:127.0.0.1' }, headers: { 'x-forwarded-for': '192.0.2.1' } } as never), '127.0.0.1');
});

test('ACA exact HTTPS origin works with secure sessions; proxy headers cannot authorize another origin', async (t) => {
  const origin = 'https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io';
  const f = await fixture(t, { config: { ...config, publicOrigin: origin } });
  const spoof = { 'X-Forwarded-Host': new URL(origin).host, 'X-Forwarded-Proto': 'https',
    Forwarded: `host=${new URL(origin).host};proto=https` };
  for (const invalid of ['https://chat.example', origin + '.evil.invalid', origin.replace('https:', 'http:')]) {
    assert.equal((await f.post('/api/chat', { message: 'hi' }, undefined,
      { ...spoof, Origin: invalid })).status, 403);
  }
  const accepted = await f.post('/api/chat', { message: 'hi' }, undefined, { ...spoof, Origin: origin });
  assert.equal(accepted.status, 200);
  assert.match(accepted.headers.get('set-cookie')!, /; Secure$/);
  const continued = await f.post('/api/chat', { message: 'again' }, cookie(accepted), { Origin: origin });
  assert.equal((await continued.json()).continued, true);
});

test('bounded stores reject capacity rather than evict active protections; TTL frees inactive sessions', () => {
  let time = 0;
  const sessions = new Sessions(() => time, 1);
  const old = sessions.create();
  assert.throws(() => sessions.create(), /busy/);
  old.busy = true;
  time += LIMITS.sessionTtlMs;
  assert.throws(() => sessions.create(), /busy/);
  old.busy = false;
  assert.notEqual(sessions.create().id, old.id);
  const limiter = new RateLimiter(() => time, 1);
  limiter.take('127.0.0.1');
  assert.throws(() => limiter.take('192.0.2.1'), /busy/);
  time += 60_000;
  assert.doesNotThrow(() => limiter.take('192.0.2.1'));
});

test('healthz is process-only; API health is actual probe state and public config has no endpoints', async (t) => {
  const f = await fixture(t);
  assert.deepEqual(await (await fetch(`${f.base}/healthz`)).json(), { status: 'alive' });
  const response = await fetch(`${f.base}/api/health`);
  assert.equal((await response.json()).status, 'healthy');
  const publicConfig = await (await fetch(`${f.base}/api/config`)).json();
  assert.deepEqual(Object.keys(publicConfig).sort(), ['inputCharacters', 'requestsPerMinute', 'sessionMinutes', 'turns']);
});

test('production static serving restricts paths and adds CSP, HTTPS and no-store protections', async (t) => {
  const f = await fixture(t);
  const response = await fetch(f.base);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /Static fixture/);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.match(response.headers.get('content-security-policy')!, /connect-src 'self'/);
  assert.match(response.headers.get('content-security-policy')!, /frame-ancestors 'none'/);
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
  assert.equal(response.headers.get('strict-transport-security'), 'max-age=31536000');
  assert.equal(response.headers.get('access-control-allow-origin'), null);
  const asset = await fetch(`${f.base}/assets/app-test.js`);
  assert.equal(asset.status, 200);
  assert.match(asset.headers.get('cache-control')!, /immutable/);
  assert.match(asset.headers.get('content-type')!, /javascript/);
  assert.equal((await fetch(`${f.base}/assets/app-test.js`, { method: 'HEAD' })).status, 200);
  for (const pathname of ['/package.json', '/server/index.ts', '/node_modules/react/index.js', '/.env', '/assets/../../package.json', '/api/model']) {
    assert.equal((await fetch(`${f.base}${pathname}`)).status, 404);
  }
});
