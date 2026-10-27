import { AIProjectClient, type KnownApiVersions, type AgentReference } from '@azure/ai-projects';
import { AzureCliCredential, ManagedIdentityCredential } from '@azure/identity';
import { setLogLevel } from '@azure/logger';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type { Config } from './config.js';
import { AppError, LIMITS, type Agent, type AgentRequest, type Probe } from './contracts.js';
import { groundedReply, parseToolOutput, validateAnalysis } from './grounding.js';

export const ALLOWED_TOOLS = ['get_data_context', 'analyze_data'] as const;

export function agentPayload(config: Config, request: AgentRequest) {
  const reference: AgentReference = {
    name: config.agentName, type: 'agent_reference',
    ...(config.agentVersion ? { version: config.agentVersion } : {}),
  };
  return {
    request: {
      input: request.message,
      ...(request.previousResponseId ? { previous_response_id: request.previousResponseId } : {}),
      max_tool_calls: LIMITS.toolCalls,
      stream: false as const,
      store: true,
    },
    options: {
      body: { agent_reference: reference },
      signal: request.signal,
      timeout: LIMITS.chatTimeoutMs,
      maxRetries: 0,
    },
  };
}

type OpenAIClient = ReturnType<AIProjectClient['getOpenAIClient']>;
type ProviderResponse = Pick<Awaited<ReturnType<OpenAIClient['responses']['retrieve']>>,
  'id' | 'output_text' | 'status' | 'output' | 'incomplete_details'>;
export type ResponseCaller = (
  payload: ReturnType<typeof agentPayload>,
) => Promise<ProviderResponse>;

export function createResponseCaller(
  config: Config,
  credential: ConstructorParameters<typeof AIProjectClient>[1],
): ResponseCaller {
  return async ({ request, options }) => {
    const boundCredential = {
      getToken: (scopes: string | string[], tokenOptions?: Parameters<typeof credential.getToken>[1]) =>
        credential.getToken(scopes, {
          ...tokenOptions,
          abortSignal: options.signal,
        }),
    };
    const project = new AIProjectClient(config.projectEndpoint, boundCredential, {
      apiVersion: 'v1' as KnownApiVersions,
      retryOptions: { maxRetries: 0 },
    });
    const openai = project.getOpenAIClient({
      maxRetries: 0,
      timeout: LIMITS.chatTimeoutMs,
      logLevel: 'off',
    });
    return openai.responses.create(request, options);
  };
}

export function createAgent(config: Config, caller?: ResponseCaller): Agent {
  setLogLevel();
  const credential = config.production
    ? new ManagedIdentityCredential({
      retryOptions: { maxRetries: 0 },
      additionalPolicies: [{
        position: 'perCall',
        policy: {
          name: 'identityNetworkDeadline',
          sendRequest(request, next) { request.timeout = 10_000; return next(request); },
        },
      }],
    })
    : new AzureCliCredential({ processTimeoutInMs: 10_000 });
  const call = caller ?? createResponseCaller(config, credential);
  return async (request) => {
    try {
      const result = await call(agentPayload(config, request));
      if (result.status !== 'completed') {
        throw new AppError(503, result.incomplete_details?.reason === 'max_output_tokens'
          ? 'AGENT_OUTPUT_LIMIT' : 'AGENT_INCOMPLETE');
      }
      const toolCalls = result.output.filter((item) => item.type === 'mcp_call');
      if (toolCalls.length > LIMITS.toolCalls) throw new AppError(503, 'AGENT_TOOL_LIMIT');
      if (result.output.some((item) => item.type === 'mcp_approval_request') ||
          toolCalls.some((item) => !ALLOWED_TOOLS.includes(item.name as typeof ALLOWED_TOOLS[number]))) {
        throw new AppError(503, 'AGENT_INVALID_RESPONSE');
      }
      if (toolCalls.some((item) => item.error || item.status === 'failed')) {
        throw new AppError(503, 'AGENT_TOOL_REJECTED');
      }
      if (toolCalls.some((item) => item.status !== undefined && item.status !== 'completed')) {
        throw new AppError(503, 'AGENT_INCOMPLETE');
      }
      const analyses = [];
      for (const item of toolCalls) {
        const value = parseToolOutput(item.output);
        if (item.name === 'analyze_data') analyses.push(validateAnalysis(value));
        else if (value.version !== '1' || value.schema !== 'oge_synthetic' ||
            !value.datasets || typeof value.datasets !== 'object' || Array.isArray(value.datasets)) {
          throw new AppError(503, 'AGENT_INVALID_RESPONSE');
        }
      }
      const answer = groundedReply(result.output_text, analyses);
      if (!result.id) throw new AppError(502, 'EMPTY_REPLY');
      return {
        id: result.id, ...answer,
        toolNames: toolCalls.map((item) => item.name),
      };
    } catch (error) {
      if (error instanceof AppError) throw error;
      const status = error && typeof error === 'object' && 'status' in error ? error.status : undefined;
      if (status === 401 || status === 403) {
        console.error(JSON.stringify({ event: 'agent_authorization_failed', upstreamStatus: status }));
        throw new AppError(503, 'AGENT_FORBIDDEN');
      }
      if (status === 429) throw new AppError(503, 'AGENT_RATE_LIMITED');
      const code = error && typeof error === 'object' && 'code' in error ? error.code : undefined;
      const nested = error && typeof error === 'object' && 'error' in error ? error.error : undefined;
      const nestedCode = nested && typeof nested === 'object' && 'code' in nested ? nested.code : undefined;
      if (status === 400 && (code === 'tool_user_error' || nestedCode === 'tool_user_error')) {
        const message = error instanceof Error ? error.message : '';
        // Recognize only the observed Pydantic rule; never forward its input values or raw message.
        const groupLimit = /(?:^|\n)[ \t]*plan\.group_by[ \t]*\r?\n[ \t]*List should have at most 2 items\b/.test(message);
        throw new AppError(503, groupLimit ? 'ANALYSIS_GROUP_LIMIT' : 'AGENT_TOOL_REJECTED');
      }
      throw new AppError(503, 'AGENT_UNAVAILABLE');
    }
  };
}

export function createProbe(url: string): Probe {
  return async (signal) => {
    const client = new Client({ name: 'redshift-chat-health', version: '0.1.0' });
    const transport = new StreamableHTTPClientTransport(new URL(url), {
      fetch: (input, init) => fetch(input, {
        ...init, redirect: 'error',
        signal: AbortSignal.any([signal, ...(init?.signal ? [init.signal] : [])]),
      }),
      reconnectionOptions: {
        maxRetries: 0, initialReconnectionDelay: 1000,
        maxReconnectionDelay: 1000, reconnectionDelayGrowFactor: 1,
      },
    });
    const closeOnAbort = () => { void transport.close(); };
    signal.addEventListener('abort', closeOnAbort, { once: true });
    try {
      signal.throwIfAborted();
      await client.connect(transport, { signal, timeout: LIMITS.healthTimeoutMs });
      const result = await client.callTool(
        { name: 'test_connection', arguments: {} },
        undefined,
        { signal, timeout: LIMITS.healthTimeoutMs },
      );
      if (result.isError) return false;
      if (result.structuredContent && typeof result.structuredContent === 'object') {
        return 'connected' in result.structuredContent && result.structuredContent.connected === true;
      }
      return Array.isArray(result.content) && result.content.some((item) => {
        if (item.type !== 'text' || typeof item.text !== 'string') return false;
        try {
          const body: unknown = JSON.parse(item.text);
          return !!body && typeof body === 'object' && 'connected' in body && body.connected === true;
        } catch { return false; }
      });
    } finally {
      try {
        if (!signal.aborted) await transport.terminateSession();
      } finally {
        await client.close();
        await transport.close();
        signal.removeEventListener('abort', closeOnAbort);
      }
    }
  };
}
