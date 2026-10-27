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
  SESSION_EXPIRED: 'This conversation expired after 30 minutes or was lost when the app restarted or was updated. Refreshing the page does not replace its cookie. Start a new chat; earlier context cannot be restored.',
  SESSION_BUSY: 'An answer is already being prepared for this conversation.',
  TURN_LIMIT: 'This conversation reached its 20-turn limit. Start a new chat.',
  CHAT_TIMEOUT: 'The answer timed out. Start a new chat; the provider may still retain this attempt.',
  ANALYSIS_GROUP_LIMIT: 'The agent requested more than two grouping fields, but the MCP analytics tool supports at most two per analysis (well, state, basin or operator). Ask for one or two fields, or split the question. No verified answer was returned for this attempt.',
  AGENT_TOOL_REJECTED: 'Foundry reported that an MCP tool call failed or was rejected. No verified answer was returned. Rephrase using supported production/cost totals, well counts or monthly prices; raw SQL and custom ratios, revenue and data-quality checks are not supported.',
  AGENT_TOOL_LIMIT: 'The agent exceeded the four-tool-call budget for one answer. Split the request into smaller questions; no verified answer was returned.',
  AGENT_OUTPUT_LIMIT: 'The model reached its own output-token limit before completing the response. No partial answer was shown. Ask a narrower question or request a shorter answer.',
  AGENT_INCOMPLETE: 'Foundry did not finish the agent response. No incomplete answer was shown. Try a smaller, focused question.',
  AGENT_INVALID_RESPONSE: 'The agent response failed the app\'s output-format, permitted-tool or fresh-data verification checks. No unverified data answer was shown. Try a focused question about supported production, wells or monthly prices.',
  AGENT_RATE_LIMITED: 'Foundry is temporarily limiting requests. Wait before trying again; each attempt uses a turn.',
  AGENT_UNAVAILABLE: 'Foundry could not complete this attempt. The app has no more specific failure reason; this does not establish that Redshift is disconnected. Please try again later.',
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
