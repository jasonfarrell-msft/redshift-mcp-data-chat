import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { isIP } from 'node:net';
import path from 'node:path';
import type { Config } from './config.js';
import { AppError, ERRORS, LIMITS, type Agent, type AgentReply, type ChatReply } from './contracts.js';
import { HealthMonitor } from './health.js';
import { RateLimiter, Sessions, type Session } from './state.js';

type Options = {
  config: Config;
  agent: Agent;
  health: HealthMonitor;
  clientDir: string;
  now?: () => number;
  sessions?: Sessions;
  limiter?: RateLimiter;
  chatTimeoutMs?: number;
  log?: (code: string) => void;
};

export function clientIp(req: IncomingMessage): string {
  // Hosting-proxy forwarding is not an authenticated, app-configured trust boundary.
  // Ignore ALL client/proxy forwarding headers; aggregate on the verified socket.
  const address = req.socket.remoteAddress ?? 'unknown';
  return isIP(address) ? address.replace(/^::ffff:/, '') : 'unknown';
}

function cookieName(config: Config): string {
  return config.production ? '__Host-redshift-chat' : 'redshift-chat-dev';
}

function sessionId(req: IncomingMessage, config: Config): string | undefined {
  const name = cookieName(config);
  const candidates = (req.headers.cookie ?? '').split(';').map((part) => part.trim())
    .filter((part) => part.startsWith(`${name}=`));
  if (!candidates.length) return undefined;
  const value = candidates[0]?.slice(name.length + 1);
  if (candidates.length !== 1 || !value || !/^[\w-]{43}$/.test(value)) {
    throw new AppError(409, 'SESSION_EXPIRED');
  }
  return value;
}

function setCookie(res: ServerResponse, config: Config, session: Session, now: number): void {
  res.setHeader('Set-Cookie', `${cookieName(config)}=${session.id}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${
    Math.max(0, Math.floor((session.expiresAt - now) / 1000))
  }${config.production ? '; Secure' : ''}`);
}

function json(res: ServerResponse, status: number, body: unknown): void {
  if (res.destroyed || res.writableEnded) return;
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

function readJson(req: IncomingMessage): Promise<unknown> {
  if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(req.headers['content-type'] ?? '') ||
      req.headers['content-encoding']) throw new AppError(415, 'BAD_REQUEST');
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let size = 0;
    const cleanup = () => {
      clearTimeout(timer);
      req.off('data', onData);
      req.off('end', onEnd);
      req.off('error', onError);
      req.off('aborted', onError);
    };
    const fail = (error: AppError) => { cleanup(); req.resume(); reject(error); };
    const onData = (chunk: Buffer) => {
      size += chunk.length;
      if (size > LIMITS.requestBytes) { fail(new AppError(413, 'BODY_TOO_LARGE')); return; }
      chunks.push(chunk);
    };
    const onError = () => fail(new AppError(400, 'BAD_REQUEST'));
    const onEnd = () => {
      cleanup();
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')) as unknown); }
      catch { reject(new AppError(400, 'BAD_REQUEST')); }
    };
    const timer = setTimeout(() => fail(new AppError(408, 'BAD_REQUEST')), 10_000);
    req.on('data', onData);
    req.on('end', onEnd);
    req.on('error', onError);
    req.on('aborted', onError);
  });
}

function objectWithKeys(value: unknown, keys: string[]): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && Object.keys(value).every((key) => keys.includes(key));
}

export function createApp(options: Options) {
  const { config, agent, health } = options;
  const now = options.now ?? Date.now;
  const sessions = options.sessions ?? new Sessions(now);
  const limiter = options.limiter ?? new RateLimiter(now);
  const controllers = new Set<AbortController>();
  const log = options.log ?? ((code: string) => console.warn(JSON.stringify({ event: 'request_failed', code })));
  let active = 0;

  async function chat(req: IncomingMessage, res: ServerResponse, session: Session, message: string) {
    if (session.busy) throw new AppError(409, 'SESSION_BUSY');
    if (session.uncertain) throw new AppError(409, 'CHAT_TIMEOUT');
    if (session.turns >= LIMITS.turns) throw new AppError(409, 'TURN_LIMIT');
    if (active >= LIMITS.concurrentChats) throw new AppError(503, 'CAPACITY');
    // No await between checks and reservation: concurrent HTTP requests cannot bypass this.
    active++;
    session.busy = true;
    session.turns++;
    const controller = new AbortController();
    controllers.add(controller);
    const disconnected = () => { if (!res.writableEnded) controller.abort(); };
    res.on('close', disconnected);
    const previousResponseId = session.previousResponseId;
    const work = Promise.resolve().then(() => agent({
      message, previousResponseId, signal: controller.signal,
    }));
    const release = work.finally(() => {
      active--;
      session.busy = false;
      controllers.delete(controller);
    });
    // Observe eventual failure even when an SDK ignores cancellation. Keep its slot quarantined.
    void release.catch(() => {});
    let timer: ReturnType<typeof setTimeout> | undefined;
    let onAbort: (() => void) | undefined;
    const deadline = new Promise<AgentReply>((_, reject) => {
      onAbort = () => {
        session.uncertain = true;
        reject(new AppError(504, 'CHAT_TIMEOUT'));
      };
      controller.signal.addEventListener('abort', onAbort, { once: true });
      timer = setTimeout(() => controller.abort(), options.chatTimeoutMs ?? LIMITS.chatTimeoutMs);
    });
    try {
      const answer = await Promise.race([work, deadline]);
      session.previousResponseId = answer.id;
      json(res, 200, {
        reply: answer.reply, turnsRemaining: LIMITS.turns - session.turns,
        truncated: answer.truncated, expiresAt: new Date(session.expiresAt).toISOString(),
        toolNames: answer.toolNames, continued: !!previousResponseId,
      } satisfies ChatReply);
    } finally {
      if (timer) clearTimeout(timer);
      if (onAbort) controller.signal.removeEventListener('abort', onAbort);
      res.off('close', disconnected);
    }
  }

  async function serveStatic(req: IncomingMessage, res: ServerResponse, pathname: string) {
    if (req.method !== 'GET' && req.method !== 'HEAD') throw new AppError(404, 'NOT_FOUND');
    // Only build artifacts are served: no source, dependency, configuration, or dot files.
    const isIndex = pathname === '/' || pathname === '/index.html';
    if (!isIndex && !/^\/assets\/[a-zA-Z0-9_-]+\.(js|css|woff2|svg)$/.test(pathname)) {
      throw new AppError(404, 'NOT_FOUND');
    }
    const file = path.join(options.clientDir, isIndex ? 'index.html' : pathname.slice(1));
    let size: number;
    try { size = (await stat(file)).size; }
    catch { throw new AppError(404, 'NOT_FOUND'); }
    const type: Record<string, string> = {
      '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
    };
    res.writeHead(200, {
      'Content-Type': type[path.extname(file)] ?? 'application/octet-stream',
      'Content-Length': size,
      'Cache-Control': isIndex ? 'no-store' : 'public, max-age=31536000, immutable',
    });
    if (req.method === 'HEAD') { res.end(); return; }
    const stream = createReadStream(file);
    stream.on('error', () => res.destroy());
    res.on('close', () => stream.destroy());
    stream.pipe(res);
  }

  const server = createServer({ maxHeaderSize: 8192, requestTimeout: 15_000, headersTimeout: 10_000 },
    (req, res) => {
      res.setHeader('Cache-Control', 'no-store');
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('Referrer-Policy', 'no-referrer');
      res.setHeader('X-Frame-Options', 'DENY');
      res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
      res.setHeader('Content-Security-Policy',
        "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
      if (config.production) res.setHeader('Strict-Transport-Security', 'max-age=31536000');
      let session: Session | undefined;
      void (async () => {
        const url = new URL(req.url ?? '/', 'http://internal.invalid');
        if (url.search) throw new AppError(400, 'BAD_REQUEST');
        const route = url.pathname;
        if (route === '/healthz' && req.method === 'GET') {
          json(res, 200, { status: 'alive' });
          return;
        }
        if (!route.startsWith('/api/')) { await serveStatic(req, res, route); return; }
        limiter.take(clientIp(req));
        if (req.headers['sec-fetch-site'] === 'cross-site') throw new AppError(403, 'ORIGIN_REJECTED');
        if (req.method === 'GET' && route === '/api/config') {
          json(res, 200, {
            inputCharacters: LIMITS.inputCharacters, turns: LIMITS.turns,
            requestsPerMinute: LIMITS.requestsPerMinute, sessionMinutes: 30,
          });
          return;
        }
        if (req.method === 'GET' && route === '/api/health') {
          const state = await health.check();
          json(res, state.status === 'unavailable' ? 503 : 200, state);
          return;
        }
        if (req.method !== 'POST' || !['/api/chat', '/api/session/reset'].includes(route)) {
          throw new AppError(404, 'NOT_FOUND');
        }
        if (req.headers.origin !== config.publicOrigin) throw new AppError(403, 'ORIGIN_REJECTED');
        const body = await readJson(req);
        if (route === '/api/session/reset') {
          if (!objectWithKeys(body, [])) throw new AppError(400, 'BAD_REQUEST');
          let id: string | undefined;
          try { id = sessionId(req, config); }
          catch { /* Reset is the only recovery for a malformed or lost cookie. */ }
          session = sessions.reset(id);
          setCookie(res, config, session, now());
          json(res, 200, { turnsRemaining: LIMITS.turns, expiresAt: new Date(session.expiresAt).toISOString() });
          return;
        }
        if (!objectWithKeys(body, ['message']) || typeof body.message !== 'string' ||
            !body.message.trim() || body.message.length > LIMITS.inputCharacters) {
          throw new AppError(400, 'BAD_REQUEST');
        }
        const id = sessionId(req, config);
        session = id ? sessions.get(id) : sessions.create();
        if (!id) setCookie(res, config, session, now());
        await chat(req, res, session, body.message.trim());
      })().catch((error: unknown) => {
        const safe = error instanceof AppError ? error : new AppError(500, 'INTERNAL');
        if (safe.status >= 500) log(safe.code);
        if (safe.status === 429) res.setHeader('Retry-After', '60');
        if (!req.complete) res.setHeader('Connection', 'close');
        json(res, safe.status, {
          error: { code: safe.code, message: ERRORS[safe.code] },
          ...(session ? { turnsRemaining: Math.max(0, LIMITS.turns - session.turns) } : {}),
        });
      });
    });
  server.keepAliveTimeout = 5000;
  server.maxRequestsPerSocket = 100;
  return {
    server,
    close: () => {
      health.close();
      for (const controller of controllers) controller.abort();
      server.closeIdleConnections();
      return new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    },
  };
}
