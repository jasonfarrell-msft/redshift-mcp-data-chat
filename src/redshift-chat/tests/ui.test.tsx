import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { renderToStaticMarkup } from 'react-dom/server';
import App from '../client/App.js';
import { ApiError, request, shouldSend, validHealth } from '../client/api.js';
import { ConnectionStatus, ErrorNotice, MessageBubble } from '../client/components.js';

test('assistant/user replies render escaped plain text, never HTML, Markdown, or clickable links', () => {
  for (const role of ['user', 'assistant'] as const) {
    const html = renderToStaticMarkup(<MessageBubble message={{
      id: '1', role, text: '<script>alert("unsafe")</script>\n[click](javascript:alert(1))',
    }} />);
    assert.match(html, /&lt;script&gt;/);
    assert.doesNotMatch(html, /<script|href=|dangerouslySetInnerHTML/);
    assert.match(html, role === 'user' ? /You message/ : /Assistant message/);
  }
});

test('assistant replies display the Redshift Analytics speaker label, not the old explorer label', () => {
  const html = renderToStaticMarkup(<MessageBubble message={{
    id: 'reply-1', role: 'assistant', text: 'Oil production totaled 125 barrels.',
  }} />);
  assert.match(html, /<span class="message-role">Redshift Analytics<\/span>/);
  assert.doesNotMatch(html, /Redshift Explorer/);
});

test('all health states are explicit; stale/unavailable never claim connected', () => {
  for (const [status, label] of [
    ['healthy', 'Redshift connected'], ['checking', 'Checking Redshift'],
    ['stale', 'Last check expired'], ['unavailable', 'Redshift unavailable'],
  ] as const) {
    const html = renderToStaticMarkup(<ConnectionStatus health={{
      status, connected: status === 'healthy', checkedAt: '2026-10-26T17:00:00Z',
    }} refreshing={false} onRefresh={() => {}} />);
    assert.ok(html.includes(label));
    assert.match(html, /role="status"/);
    assert.match(html, /Check again/);
  }
  assert.equal(validHealth({ status: 'healthy', connected: false, checkedAt: null }), false);
  assert.equal(validHealth({ status: 'unknown', connected: true, checkedAt: null }), false);
});

test('safe error state announces failure, with explicit nonautomatic retry using another turn', () => {
  const html = renderToStaticMarkup(<ErrorNotice error={new ApiError('AGENT_FORBIDDEN')} canRetry onRetry={() => {}} />);
  assert.match(html, /role="alert"/);
  assert.match(html, /managed-identity project access/);
  assert.match(html, /uses another turn/);
  const expired = renderToStaticMarkup(<ErrorNotice error={new ApiError('SESSION_EXPIRED')} canRetry={false} onRetry={() => {}} />);
  assert.doesNotMatch(expired, /<button/);
});

test('keyboard Enter submits, Shift+Enter inserts a line, and IME composition never submits', () => {
  assert.equal(shouldSend({ key: 'Enter', shiftKey: false, nativeEvent: {} }), true);
  assert.equal(shouldSend({ key: 'Enter', shiftKey: true, nativeEvent: {} }), false);
  assert.equal(shouldSend({ key: 'Enter', shiftKey: false, nativeEvent: { isComposing: true } }), false);
  assert.equal(shouldSend({ key: 'a', shiftKey: false, nativeEvent: {} }), false);
});

test('initial app includes accessible composer, role log, privacy/retention and plan safety notices', () => {
  const html = renderToStaticMarkup(<App />);
  for (const text of [
    'role="log"', 'aria-live="polite"', 'for="message"', 'maxLength="2000"', 'New chat',
    'PUBLIC POC', 'Synthetic-data demo.', 'Don’t share sensitive information.',
    'arbitrary SQL is never accepted.',
    'Chats are processed and may be retained in Foundry', 'does not delete provider-side responses',
    '20 / 20 turns remaining', 'Shift + Enter', 'not a spending cap', 'no persistent history',
    '30-minute chains', '5 requests/minute, shared with health and reset', 'retries use a turn',
    'In-memory POC limits reset on restart',
  ]) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /https:\/\/.*\.services\.ai\.azure/);
});

test('initial UI is client-neutral and asks business questions against real data', () => {
  const html = renderToStaticMarkup(<App />);
  for (const text of [
    'Redshift Analytics home', 'YOUR DATASET', 'Redshift dataset', 'DATASET ANALYTICS',
    '<h1>Ask your data a question.</h1>', 'Questions in.',
    'Data-backed answers out.', 'Revenue and profit calculations are not supported.',
    '>How much oil was produced in 2025?<', '>Which five wells produced the most gas in 2025?<',
    '>What was the average oil price in 2025?<',
    'Ask about production, wells or prices…',
    'Ask about production, wells or prices</label>',
  ]) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /next[\s_-]*era|YOUR WORKSPACE|Is Redshift connected\?|Powered by/i);
});

test('document title and description are client-neutral and analytics-focused', () => {
  const html = readFileSync(new URL('../client/index.html', import.meta.url), 'utf8');
  assert.match(html, /<title>Redshift Analytics · Data-backed answers<\/title>/);
  assert.match(html, /name="description" content="Ask questions about synthetic production, wells and prices with read-only, data-backed Redshift analytics\."/);
  assert.doesNotMatch(html, /next[\s_-]*era|powered by/i);
});

test('client API sends only message JSON with same-origin credentials, and uses fixed safe errors', async (t) => {
  let requests = 0;
  t.mock.method(globalThis, 'fetch', async (route: string, options: RequestInit) => {
    requests++;
    assert.equal(route, '/api/chat');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.body, '{"message":"hello"}');
    return Response.json({ error: { code: 'AGENT_FORBIDDEN', message: 'SECRET raw error' }, turnsRemaining: 19 }, { status: 503 });
  });
  await assert.rejects(() => request('/api/chat', { message: 'hello' }), (error: unknown) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.code, 'AGENT_FORBIDDEN');
    assert.equal(error.turnsRemaining, 19);
    assert.doesNotMatch(error.message, /SECRET/);
    return true;
  });
  assert.equal(requests, 1);
});

test('client network/invalid JSON/unrecognized error states are safe, never automatic retries', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => { throw new Error('SECRET'); });
  await assert.rejects(() => request('/api/chat', { message: 'hello' }), /Could not reach the app/);
  fetchMock.mock.mockImplementation(async () => new Response('<b>proxy error</b>', { status: 502 }) as never);
  await assert.rejects(() => request('/api/chat', { message: 'hello' }), /Could not reach the app/);
  fetchMock.mock.mockImplementation(async () => Response.json({ error: { code: 'SECRET' } }, { status: 500 }) as never);
  await assert.rejects(() => request('/api/chat', { message: 'hello' }), /Could not reach the app/);
});
