import { LIMITS, type HealthState, type Probe } from './contracts.js';

export class HealthMonitor {
  private cached: HealthState | undefined;
  private cachedAt = 0;
  private inFlight: Promise<HealthState> | undefined;
  private readonly controllers = new Set<AbortController>();

  constructor(
    private readonly probe: Probe,
    private readonly now = Date.now,
    private readonly timeoutMs: number = LIMITS.healthTimeoutMs,
    private readonly cacheMs: number = LIMITS.healthCacheMs,
  ) {}

  async check(): Promise<HealthState> {
    if (this.cached && this.now() - this.cachedAt < this.cacheMs) return this.cached;
    if (this.inFlight) return this.inFlight;
    const flight = this.run();
    this.inFlight = flight;
    return flight;
  }

  private async run(): Promise<HealthState> {
    const controller = new AbortController();
    this.controllers.add(controller);
    let timer: ReturnType<typeof setTimeout> | undefined;
    let timedOut = false;
    const timeout = new Promise<boolean>((resolve) => {
      timer = setTimeout(() => {
        timedOut = true;
        controller.abort();
        resolve(false);
      }, this.timeoutMs);
    });
    // The single-flight lock survives the public deadline until transport cleanup settles.
    const work = Promise.resolve().then(() => this.probe(controller.signal));
    const settled = work.catch(() => false).finally(() => {
      if (timer) clearTimeout(timer);
      this.controllers.delete(controller);
      this.inFlight = undefined;
    });
    const connected = await Promise.race([settled, timeout]);
    const result: HealthState = {
      status: connected && !timedOut ? 'healthy' : 'unavailable',
      connected: connected && !timedOut,
      checkedAt: new Date(this.now()).toISOString(),
    };
    this.cached = result;
    this.cachedAt = this.now();
    return result;
  }

  close(): void {
    for (const controller of this.controllers) controller.abort();
  }
}
