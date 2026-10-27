import { randomBytes } from 'node:crypto';
import { AppError, LIMITS } from './contracts.js';

export type Session = {
  id: string;
  expiresAt: number;
  turns: number;
  busy: boolean;
  uncertain: boolean;
  previousResponseId?: string;
};

export class Sessions {
  private readonly entries = new Map<string, Session>();
  constructor(private readonly now = Date.now, private readonly max: number = LIMITS.sessions) {}

  sweep(): void {
    for (const [id, session] of this.entries) {
      if (session.expiresAt <= this.now() && !session.busy) this.entries.delete(id);
    }
  }

  create(): Session {
    this.sweep();
    if (this.entries.size >= this.max) throw new AppError(503, 'CAPACITY');
    const session: Session = {
      id: randomBytes(32).toString('base64url'), expiresAt: this.now() + LIMITS.sessionTtlMs,
      turns: 0, busy: false, uncertain: false,
    };
    this.entries.set(session.id, session);
    return session;
  }

  get(id: string): Session {
    const session = this.entries.get(id);
    if (!session || session.expiresAt <= this.now()) {
      if (session && !session.busy) this.entries.delete(id);
      throw new AppError(409, 'SESSION_EXPIRED');
    }
    return session;
  }

  reset(id?: string): Session {
    const old = id ? this.entries.get(id) : undefined;
    if (old?.busy) throw new AppError(409, 'SESSION_BUSY');
    if (id) this.entries.delete(id);
    return this.create();
  }
}

export class RateLimiter {
  private readonly entries = new Map<string, { count: number; expiresAt: number }>();
  constructor(
    private readonly now = Date.now,
    private readonly maxEntries: number = LIMITS.rateEntries,
    private readonly requests: number = LIMITS.requestsPerMinute,
  ) {}

  take(ip: string): void {
    const time = this.now();
    for (const [key, entry] of this.entries) {
      if (entry.expiresAt <= time) this.entries.delete(key);
    }
    const existing = this.entries.get(ip);
    if (existing) {
      if (existing.count >= this.requests) throw new AppError(429, 'RATE_LIMITED');
      existing.count++;
      return;
    }
    if (this.entries.size >= this.maxEntries) throw new AppError(503, 'CAPACITY');
    this.entries.set(ip, { count: 1, expiresAt: time + 60_000 });
  }
}
