export type Config = {
  production: boolean;
  port: number;
  publicOrigin: string;
  projectEndpoint: string;
  agentName: string;
  agentVersion?: string;
  mcpUrl: string;
};

function httpsUrl(value: string | undefined, name: string): URL {
  if (!value) throw new Error(`Missing ${name}`);
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error(`Invalid ${name}`);
  }
  return url;
}

export function readConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const production = env.NODE_ENV !== 'development';
  const origin = new URL(env.PUBLIC_ORIGIN ?? (production ? '' : 'http://127.0.0.1:5173'));
  if (origin.origin !== env.PUBLIC_ORIGIN && (production || env.PUBLIC_ORIGIN)) {
    throw new Error('PUBLIC_ORIGIN must be an exact origin without a trailing slash');
  }
  if ((production && origin.protocol !== 'https:') ||
      (!production && !['localhost', '127.0.0.1'].includes(origin.hostname))) {
    throw new Error('Invalid PUBLIC_ORIGIN');
  }
  const project = httpsUrl(env.FOUNDRY_PROJECT_ENDPOINT, 'FOUNDRY_PROJECT_ENDPOINT');
  if (!project.hostname.endsWith('.services.ai.azure.com') ||
      !/^\/api\/projects\/[a-zA-Z0-9_-]+\/?$/.test(project.pathname)) {
    throw new Error('Invalid FOUNDRY_PROJECT_ENDPOINT');
  }
  const mcp = httpsUrl(env.MCP_SERVER_URL, 'MCP_SERVER_URL');
  const port = Number(env.PORT ?? 8080);
  const agentName = env.FOUNDRY_AGENT_NAME ?? 'redshift-chat-agent';
  if (!Number.isInteger(port) || port < 1 || port > 65535 ||
      !/^[a-zA-Z0-9_-]{1,128}$/.test(agentName) ||
      (env.FOUNDRY_AGENT_VERSION && !/^[a-zA-Z0-9._-]{1,64}$/.test(env.FOUNDRY_AGENT_VERSION))) {
    throw new Error('Invalid runtime configuration');
  }
  return {
    production, port, publicOrigin: origin.origin, projectEndpoint: project.href.replace(/\/$/, ''),
    mcpUrl: mcp.href, agentName, agentVersion: env.FOUNDRY_AGENT_VERSION || undefined,
  };
}
