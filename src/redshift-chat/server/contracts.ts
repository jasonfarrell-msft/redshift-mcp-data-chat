export const LIMITS = Object.freeze({
  inputCharacters: 32_000,
  requestBytes: 256 * 1024,
  toolCalls: 4,
  turns: 20,
  concurrentChats: 2,
  requestsPerMinute: 5,
  sessionTtlMs: 30 * 60_000,
  sessions: 1000,
  rateEntries: 10_000,
  chatTimeoutMs: 230_000,
  browserTimeoutMs: 235_000,
  healthTimeoutMs: 60_000,
  healthCacheMs: 30_000,
});

export type HealthState = {
  status: 'healthy' | 'checking' | 'stale' | 'unavailable';
  connected: boolean | null;
  checkedAt: string | null;
};

export type AgentRequest = {
  message: string;
  previousResponseId?: string;
  signal: AbortSignal;
};
export type AgentReply = { id: string; reply: string; truncated: boolean; toolNames: string[] };
export type ChatReply = {
  reply: string;
  toolNames: string[];
  continued: boolean;
  turnsRemaining: number;
  truncated: boolean;
  expiresAt: string;
};
export type Agent = (request: AgentRequest) => Promise<AgentReply>;
export type Probe = (signal: AbortSignal) => Promise<boolean>;

export const ERRORS = {
  BAD_REQUEST: 'Send a JSON object containing only a message of 1–32,000 characters.',
  BODY_TOO_LARGE: 'The request is too large.',
  ORIGIN_REJECTED: 'This request must come from this site. Reload and try again.',
  RATE_LIMITED: 'Too many requests. Wait a minute before trying again.',
  CAPACITY: 'The public demo is busy. Please try again later.',
  SESSION_EXPIRED: 'This conversation expired or the server restarted. Start a new chat.',
  SESSION_BUSY: 'An answer is already being prepared for this conversation.',
  TURN_LIMIT: 'This conversation reached its 20-turn limit. Start a new chat.',
  CHAT_TIMEOUT: 'The answer timed out. Start a new chat; the provider may still retain this attempt.',
  AGENT_UNAVAILABLE: 'The agent is unavailable. Please try again later.',
  AGENT_FORBIDDEN: 'The agent is unavailable: managed-identity project access needs operator verification.',
  EMPTY_REPLY: 'The agent did not return an answer. You may retry; each attempt uses a turn.',
  NOT_FOUND: 'This route is not available.',
  INTERNAL: 'The request could not be completed. Please try again later.',
} as const;

export class AppError extends Error {
  constructor(public status: number, public code: keyof typeof ERRORS) {
    super(ERRORS[code]);
  }
}
