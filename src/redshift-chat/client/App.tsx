import { useEffect, useRef, useState, type FormEvent } from 'react';
import { LIMITS, type ChatReply, type HealthState } from '../server/contracts.js';
import { ApiError, request, shouldSend, validHealth } from './api.js';
import { ConnectionStatus, ErrorNotice, MessageBubble, type Message } from './components.js';

const suggestions = ['How much oil was produced in 2025?', 'Which five wells produced the most gas in 2025?', 'What was the average oil price in 2025?'];
const newChainCodes = ['SESSION_EXPIRED', 'TURN_LIMIT', 'CHAT_TIMEOUT'];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [turns, setTurns] = useState<number>(LIMITS.turns);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastMessage, setLastMessage] = useState('');
  const [requiresNewChat, setRequiresNewChat] = useState(false);
  const [health, setHealth] = useState<HealthState>({ status: 'checking', connected: null, checkedAt: null });
  const [refreshing, setRefreshing] = useState(false);
  const [healthError, setHealthError] = useState('');
  const [announcement, setAnnouncement] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const locked = useRef(false);
  const healthLocked = useRef(false);
  const mounted = useRef(true);
  const lifetime = useRef(new AbortController());
  const mustReset = turns <= 0 || requiresNewChat;
  const inputTooLong = draft.length > LIMITS.inputCharacters;

  async function refreshHealth() {
    if (healthLocked.current) return;
    healthLocked.current = true;
    setRefreshing(true);
    setHealthError('');
    setHealth((old) => ({ ...old, status: 'checking', connected: null }));
    try {
      const result = await request<unknown>('/api/health', undefined, lifetime.current.signal);
      if (!validHealth(result)) throw new ApiError('NETWORK');
      if (mounted.current) setHealth(result);
    } catch (caught) {
      if (mounted.current) {
        setHealth((old) => ({ ...old, status: 'unavailable', connected: false }));
        setHealthError(caught instanceof ApiError ? caught.message : 'The connection check is unavailable.');
      }
    } finally {
      healthLocked.current = false;
      if (mounted.current) setRefreshing(false);
    }
  }

  useEffect(() => {
    mounted.current = true;
    lifetime.current = new AbortController();
    void refreshHealth();
    return () => { mounted.current = false; lifetime.current.abort(); };
  }, []);

  useEffect(() => {
    if (health.status !== 'healthy' || !health.checkedAt) return;
    const age = Date.now() - Date.parse(health.checkedAt);
    const timer = setTimeout(() => setHealth((old) =>
      old.status === 'healthy' ? { ...old, status: 'stale', connected: null } : old),
    Math.max(0, LIMITS.healthCacheMs - age));
    return () => clearTimeout(timer);
  }, [health]);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages, busy, error]);

  async function send(text: string, retry = false) {
    const message = text.trim();
    if (locked.current || !message || text.length > LIMITS.inputCharacters || mustReset) return;
    locked.current = true;
    setBusy(true);
    setError(null);
    setLastMessage(message);
    setDraft('');
    if (!retry) setMessages((old) => [...old, { id: crypto.randomUUID(), role: 'user', text: message }]);
    try {
      const result = await request<ChatReply>('/api/chat', { message }, lifetime.current.signal);
      if (!result || typeof result.reply !== 'string' || typeof result.turnsRemaining !== 'number') throw new ApiError('NETWORK');
      if (mounted.current) {
        setTurns(result.turnsRemaining);
        setMessages((old) => [...old, {
          id: crypto.randomUUID(), role: 'assistant', text: result.reply, truncated: result.truncated,
        }]);
      }
    } catch (caught) {
      if (mounted.current) {
        const safe = caught instanceof ApiError ? caught : new ApiError('NETWORK');
        setError(safe);
        if (newChainCodes.includes(safe.code)) {
          setRequiresNewChat(true);
          setDraft(message);
        }
        if (safe.turnsRemaining !== undefined) setTurns(safe.turnsRemaining);
      }
    } finally {
      locked.current = false;
      if (mounted.current) { setBusy(false); inputRef.current?.focus(); }
    }
  }

  async function reset(preserveQuestion = false) {
    if (locked.current) return;
    locked.current = true;
    setResetting(true);
    try {
      await request('/api/session/reset', {}, lifetime.current.signal);
      if (mounted.current) {
        setMessages([]);
        setDraft(preserveQuestion ? draft || lastMessage : '');
        setError(null); setTurns(LIMITS.turns); setLastMessage(''); setRequiresNewChat(false);
        setAnnouncement(preserveQuestion
          ? 'New conversation started. Your question is kept below; press Send when ready. Earlier context is not restored and provider-side responses are not deleted.'
          : 'New conversation started. This does not delete provider-side responses.');
      }
    } catch (caught) {
      if (mounted.current) setError(caught instanceof ApiError ? caught : new ApiError('NETWORK'));
    } finally {
      locked.current = false;
      if (mounted.current) { setResetting(false); inputRef.current?.focus(); }
    }
  }

  function submit(event: FormEvent) { event.preventDefault(); void send(draft); }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Redshift Analytics home">
        <span className="brand-mark" aria-hidden="true">R<span>↗</span></span>
        <span>Redshift<span className="brand-sub">ANALYTICS</span></span>
      </a>
      <div className="sidebar-content">
        <span className="eyebrow">YOUR DATASET</span>
        <div className="workspace-card"><span className="workspace-icon" aria-hidden="true">▤</span><div>Redshift dataset<span>Read-only data answers</span></div></div>
        <button className="new-chat" type="button" onClick={() => void reset()} disabled={busy || resetting}>
          <span aria-hidden="true">＋</span> {resetting ? 'Starting…' : 'New chat'}
        </button>
        <div className="sidebar-note"><strong>A conversation, not a query console.</strong><p>Ask about production, wells and monthly prices in oge_synthetic. Validated analysis plans retrieve actual data; arbitrary SQL is never accepted.</p></div>
        <ConnectionStatus health={health} refreshing={refreshing} onRefresh={() => void refreshHealth()} />
        {healthError && <p className="health-error" role="alert">{healthError} Health checks share the 5-request/minute limit.</p>}
      </div>
      <footer className="sidebar-footer"><span className="poc-badge">PUBLIC POC</span><p>Answers from synthetic data.<br />Production, wells and monthly prices.</p></footer>
    </aside>

    <main className="main-panel">
      <header className="topbar"><div><span className="eyebrow">DATASET ANALYTICS</span><h1>Ask your data a question.</h1></div><span className="read-only">Read-only</span></header>
      <div className="privacy-notice"><strong>Synthetic-data demo.</strong> Don’t share sensitive information. Chats are processed and may be retained in Foundry; this site keeps no persistent history. New chat clears this view and starts a new chain, but does not delete provider-side responses.</div>
      <section className="conversation" aria-label="Conversation">
        {!messages.length && <div className="welcome">
          <div className="welcome-mark" aria-hidden="true">✦</div>
          <span className="eyebrow">START WITH A QUESTION</span>
          <h2>Questions in.<br /><span>Data-backed answers out.</span></h2>
          <p>Ask about oil and gas production, operating costs, wells and monthly prices. Answers use observed data periods, show units and explain missing or limited results. Revenue and profit calculations are not supported.</p>
          <div className="suggestions">{suggestions.map((text) => <button key={text} type="button" disabled={busy || resetting} onClick={() => { setDraft(text); inputRef.current?.focus(); }}>{text}<span aria-hidden="true">↗</span></button>)}</div>
        </div>}
        <div className="message-log" role="log" aria-label="Chat messages" aria-live="polite" aria-relevant="additions text">
          {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
          {busy && <div className="thinking" role="status"><span className="thinking-dot" />The agent is checking its tools and preparing an answer…</div>}
        </div>
        {error && <ErrorNotice error={error} canRetry={!mustReset && !busy && !resetting && !!lastMessage}
          onRetry={() => void send(lastMessage, true)}
          onNewChat={mustReset && !busy && !resetting ? () => void reset(true) : undefined} />}
        {mustReset && <p className="reset-prompt">Use <strong>New chat</strong> to start a fresh conversation.</p>}
        <div ref={endRef} />
      </section>
      <div className="composer-wrap">
        <form className="composer" onSubmit={submit}>
          <label className="sr-only" htmlFor="message">Ask about production, wells or prices</label>
          <textarea id="message" ref={inputRef} value={draft} rows={2}
            placeholder="Ask about production, wells or prices…"
            disabled={busy || resetting || mustReset} aria-invalid={inputTooLong}
            aria-describedby={inputTooLong ? 'composer-help composer-error' : 'composer-help'}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => { if (shouldSend(event)) { event.preventDefault(); void send(draft); } }} />
          <div className="composer-bottom"><span aria-hidden="true">{draft.length.toLocaleString()} / {LIMITS.inputCharacters.toLocaleString()}</span>
            <button className="send-button" type="submit" disabled={busy || resetting || mustReset || inputTooLong || !draft.trim()}>{busy ? 'Working…' : 'Send'} <span aria-hidden="true">↑</span></button></div>
        </form>
        {inputTooLong && <p className="health-error" id="composer-error" role="alert">
          Your full prompt is preserved, but exceeds {LIMITS.inputCharacters.toLocaleString()} characters. Shorten it before sending.
        </p>}
        <div className="composer-help" id="composer-help"><span>Enter to send · Shift + Enter for a new line</span><span>{turns} / 20 turns remaining</span></div>
        <p className="limits-note">30-minute chains · 5 requests/minute, shared with health and reset · retries use a turn. In-memory POC limits reset on restart and are not a spending cap. Verify important answers.</p>
      </div>
      <div className="sr-only" role="status">{announcement}</div>
    </main>
  </div>;
}
