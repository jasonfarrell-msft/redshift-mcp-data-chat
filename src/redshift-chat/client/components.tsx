import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { HealthState } from '../server/contracts.js';
import type { ApiError } from './api.js';

export type Message = { id: string; role: 'user' | 'assistant'; text: string; truncated?: boolean };

export function MessageBubble({ message }: { message: Message }) {
  return <article className={`message ${message.role}`} aria-label={`${message.role === 'user' ? 'You' : 'Assistant'} message`}>
    <div className="avatar" aria-hidden="true">{message.role === 'user' ? 'Y' : 'R'}</div>
    <div className="message-body">
      <span className="message-role">{message.role === 'user' ? 'You' : 'Redshift Analytics'}</span>
      {message.role === 'assistant' ? <div className="markdown">
        <Markdown remarkPlugins={[remarkGfm]} skipHtml components={{
          a: ({ href, children }) => href && /^https?:\/\//i.test(href)
            ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
            : <span>{children}</span>,
          img: ({ alt }) => <span>{alt}</span>,
          table: ({ children }) => <div className="markdown-table" role="region" aria-label="Answer table" tabIndex={0}>
            <table>{children}</table>
          </div>,
          th: ({ children, style }) => <th data-align={style?.textAlign}>{children}</th>,
          td: ({ children, style }) => <td data-align={style?.textAlign}>{children}</td>,
        }}>{message.text}</Markdown>
      </div> : <p>{message.text}</p>}
      {message.truncated && <small className="truncated">Answer reached its output limit. Ask a focused follow-up for more detail.</small>}
    </div>
  </article>;
}

export function ConnectionStatus({ health, refreshing, onRefresh }: {
  health: HealthState; refreshing: boolean; onRefresh: () => void;
}) {
  const labels: Record<HealthState['status'], string> = {
    healthy: 'Redshift connected', checking: 'Checking Redshift…',
    stale: 'Last check expired', unavailable: 'Redshift unavailable',
  };
  return <section className="connection" aria-label="Redshift connection health">
    <div className={`connection-label ${health.status}`} role="status">
      <span className="status-dot" aria-hidden="true" />{labels[health.status]}
    </div>
    <div className="connection-detail">
      <span>{health.checkedAt ? `Checked ${new Date(health.checkedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}` : 'Direct read-only MCP check · no AI'}</span>
      <button type="button" className="text-button" onClick={onRefresh} disabled={refreshing}>
        {refreshing ? 'Checking…' : 'Check again'}
      </button>
    </div>
  </section>;
}

export function ErrorNotice({ error, canRetry, onRetry }: {
  error: ApiError; canRetry: boolean; onRetry: () => void;
}) {
  const titles: Partial<Record<ApiError['code'], string>> = {
    ANALYSIS_GROUP_LIMIT: 'Too many grouping fields.',
    AGENT_TOOL_REJECTED: 'The analytics tool could not complete this request.',
    AGENT_TOOL_LIMIT: 'This request exceeded the tool-call budget.',
    AGENT_OUTPUT_LIMIT: 'The model reached its output limit.',
    AGENT_INCOMPLETE: 'The agent did not finish its response.',
    AGENT_INVALID_RESPONSE: 'The answer could not be verified.',
    AGENT_RATE_LIMITED: 'Foundry is temporarily limiting requests.',
  };
  const needsRephrasing = [
    'ANALYSIS_GROUP_LIMIT', 'AGENT_TOOL_REJECTED', 'AGENT_TOOL_LIMIT',
    'AGENT_OUTPUT_LIMIT', 'AGENT_INVALID_RESPONSE',
  ].includes(error.code);
  return <div className="error-notice" role="alert">
    <div><strong>{titles[error.code] ?? 'We couldn’t complete that request.'}</strong><p>{error.message}</p><small>Error code: {error.code}</small></div>
    {canRetry && !needsRephrasing && <button type="button" onClick={onRetry}>Retry <span className="sr-only">(uses another turn)</span></button>}
  </div>;
}
