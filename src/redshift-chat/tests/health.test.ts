import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { test } from 'node:test';
import { setTimeout as sleep } from 'node:timers/promises';
import { HealthMonitor } from '../server/health.js';
import { createProbe } from '../server/providers.js';

test('health success is cached for 30 seconds; expiry is stale, not a current success', async () => {
  let time = 1_000_000;
  let calls = 0;
  const monitor = new HealthMonitor(async () => { calls++; return true; }, () => time);
  const first = await monitor.check();
  assert.deepEqual(first, { status: 'healthy', connected: true, checkedAt: new Date(time).toISOString() });
  time += 29_999;
  assert.deepEqual(await monitor.check(), first);
  assert.equal(calls, 1);
  time++;
  const stale = await monitor.check();
  assert.equal(stale.status, 'stale');
  assert.equal(stale.connected, null);
  assert.equal(stale.checkedAt, first.checkedAt);
  await sleep(1);
  assert.equal((await monitor.check()).status, 'healthy');
  assert.equal(calls, 2);
  monitor.close();
});

test('single-flight prevents overlapping probes and exposes checking', async () => {
  let resolve!: (value: boolean) => void;
  let calls = 0;
  const monitor = new HealthMonitor(async () => {
    calls++;
    return new Promise<boolean>((done) => { resolve = done; });
  });
  const first = monitor.check();
  await sleep(1);
  assert.deepEqual(await monitor.check(), { status: 'checking', connected: null, checkedAt: null });
  assert.equal(calls, 1);
  resolve(true);
  assert.equal((await first).status, 'healthy');
  monitor.close();
});

test('deadline aborts probe; hanging cleanup holds the lock past cache expiry and late success is ignored', async () => {
  let time = 1_000_000;
  let resolve!: (value: boolean) => void;
  let signal: AbortSignal | undefined;
  let calls = 0;
  const monitor = new HealthMonitor(async (abort) => {
    calls++;
    signal = abort;
    return new Promise<boolean>((done) => { resolve = done; });
  }, () => time, 15, 30);
  const result = await monitor.check();
  assert.equal(result.status, 'unavailable');
  assert.equal(signal?.aborted, true);
  assert.deepEqual(await monitor.check(), result);
  time += 31;
  assert.equal((await monitor.check()).status, 'checking');
  assert.equal(calls, 1);
  resolve(true);
  await sleep(1);
  assert.equal((await monitor.check()).status, 'stale');
  assert.equal(calls, 2);
  monitor.close();
  resolve(false);
});

test('downstream failure reports unavailable, never a fallback healthy result', async () => {
  const monitor = new HealthMonitor(async () => { throw new Error('sensitive database details'); });
  const result = await monitor.check();
  assert.equal(result.status, 'unavailable');
  assert.equal(result.connected, false);
  assert.doesNotMatch(JSON.stringify(result), /sensitive/);
  monitor.close();
});

test('official StreamableHTTP client initializes, calls ONLY test_connection, and deletes its MCP session', async (t) => {
  const methods: string[] = [];
  const tools: string[] = [];
  const sessions: (string | undefined)[] = [];
  let connected = true;
  const server = createServer((req, res) => {
    methods.push(req.method!);
    sessions.push(req.headers['mcp-session-id'] as string | undefined);
    if (req.method === 'GET') { res.writeHead(405); res.end(); return; }
    if (req.method === 'DELETE') { res.writeHead(200); res.end(); return; }
    const chunks: Buffer[] = [];
    req.on('data', (chunk: Buffer) => chunks.push(chunk));
    req.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString());
      if (!('id' in body)) { res.writeHead(202); res.end(); return; }
      let result: unknown;
      if (body.method === 'initialize') {
        result = { protocolVersion: '2025-11-25', capabilities: { tools: {} }, serverInfo: { name: 'mock-redshift', version: '1' } };
      } else if (body.method === 'tools/call') {
        tools.push(body.params.name);
        assert.deepEqual(body.params.arguments, {});
        result = { content: [{ type: 'text', text: JSON.stringify({ connected }) }], structuredContent: { connected }, isError: false };
      } else { assert.fail(`Unexpected MCP method ${body.method}`); }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Mcp-Session-Id': 'mock-session' });
      res.end(JSON.stringify({ jsonrpc: '2.0', id: body.id, result }));
    });
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => new Promise<void>((resolve) => { server.closeIdleConnections(); server.close(() => resolve()); }));
  const probe = createProbe(`http://127.0.0.1:${(server.address() as AddressInfo).port}/mcp`);
  assert.equal(await probe(AbortSignal.timeout(1000)), true);
  connected = false;
  assert.equal(await probe(AbortSignal.timeout(1000)), false);
  assert.deepEqual(tools, ['test_connection', 'test_connection']);
  assert.equal(methods.filter((method) => method === 'DELETE').length, 2);
  assert.ok(sessions.includes('mock-session'));
});

test('MCP handshake network hang is aborted and transport is closed at the health deadline', async (t) => {
  let socketClosed = false;
  const server = createServer((_req, _res) => {});
  server.on('connection', (socket) => socket.on('close', () => { socketClosed = true; }));
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => { server.closeAllConnections(); server.close(); });
  const monitor = new HealthMonitor(createProbe(`http://127.0.0.1:${(server.address() as AddressInfo).port}/mcp`), Date.now, 30);
  assert.equal((await monitor.check()).status, 'unavailable');
  for (let i = 0; i < 50 && !socketClosed; i++) await sleep(5);
  assert.equal(socketClosed, true);
  monitor.close();
});
