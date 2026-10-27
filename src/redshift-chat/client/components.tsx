import type { HealthState } from '../server/contracts.js';
import type { ApiError } from './api.js';

export type Message = { id: string; role: 'user' | 'assistant'; text: string; truncated?: boolean };

export function MessageBubble({ message }: { message: Message }) {
  return <article className={`message ${message.role}`} aria-label={`${message.role === 'user' ? 'You' : 'Assistant'} message`}>
    <div className="avatar" aria-hidden="true">{message.role === 'user' ? 'Y' : 'R'}</div>
    <div className="message-body">
      <span className="message-role">{message.role === 'user' ? 'You' : 'Redshift Analytics'}</span>
      <p>{message.text}</p>
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
  return <div className="error-notice" role="alert">
    <div><strong>We couldn’t complete that request.</strong><p>{error.message}</p></div>
    {canRetry && <button type="button" onClick={onRetry}>Retry <span className="sr-only">(uses another turn)</span></button>}
  </div>;
}
