import { fileURLToPath } from 'node:url';
import { createApp } from './app.js';
import { readConfig } from './config.js';
import { HealthMonitor } from './health.js';
import { createAgent, createProbe } from './providers.js';

try {
  const config = readConfig();
  const app = createApp({
    config,
    agent: createAgent(config),
    health: new HealthMonitor(createProbe(config.mcpUrl)),
    clientDir: fileURLToPath(new URL('../client/', import.meta.url)),
  });
  app.server.listen(config.port, '0.0.0.0', () => {
    console.info(JSON.stringify({ event: 'listening', port: config.port }));
  });
  const shutdown = () => {
    const forced = setTimeout(() => process.exit(1), 10_000);
    forced.unref();
    void app.close().then(() => { clearTimeout(forced); process.exitCode = 0; });
  };
  process.once('SIGTERM', shutdown);
  process.once('SIGINT', shutdown);
} catch {
  console.error(JSON.stringify({ event: 'startup_failed', code: 'CONFIGURATION_OR_SDK' }));
  process.exitCode = 1;
}
