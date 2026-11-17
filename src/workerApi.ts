import { v4 as uuidv4 } from "uuid";
import PyodideWorker from "./webworker?worker";

interface WorkerData {
  worker: Worker;
  requestCount: number;
  activeRequests: number;
  isInitialized: boolean;
  initPromise: Promise<void> | null;
  initStartedAt: number;
  initCompletedAt: number | null;
  workerInitDurationMs: number | null;
}

export interface WorkerPoolMetrics {
  poolSize: number;
  initializedCount: number;
  allReady: boolean;
  poolCreatedAt: number;
  firstReadyAt: number | null;
  allReadyAt: number | null;
  workers: Array<{
    index: number;
    isInitialized: boolean;
    activeRequests: number;
    requestCount: number;
    wallInitMs: number | null;
    workerInitDurationMs: number | null;
  }>;
}

function getPromiseAndResolve<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: any) => void;
  let promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function getId() {
  return uuidv4();
}

const POOL_SIZE = Math.min(
  5,
  Math.max(
    1,
    (typeof navigator !== "undefined" &&
      (navigator as any).hardwareConcurrency) ||
      2
  )
);
const MAX_REQUESTS_PER_WORKER = 50;

// Track workers with metadata
const workerPool: WorkerData[] = [];

// Track pending request resolvers by id
const pending = new Map<
  string,
  { resolve: (value: any) => void; reject: (reason?: any) => void }
>();

const poolCreatedAt = performance.now();
let firstReadyAt: number | null = null;
let allReadyAt: number | null = null;

function createWorker(): WorkerData {
  const worker = new PyodideWorker();
  const workerData: WorkerData = {
    worker,
    requestCount: 0,
    activeRequests: 0,
    isInitialized: false,
    initPromise: null,
    initStartedAt: performance.now(),
    initCompletedAt: null,
    workerInitDurationMs: null,
  };

  setupWorkerListener(workerData);
  return workerData;
}

function setupWorkerListener(workerData: WorkerData) {
  const { worker } = workerData;

  worker.addEventListener("message", (event) => {
    const data = event.data;
    if (!data || typeof data !== "object") return;
    const { id, type, ...rest } = data;

    if (id && pending.has(id)) {
      const { resolve, reject } = pending.get(id)!;
      pending.delete(id);

      if (data.error) {
        reject(new Error(data.error));
      } else {
        if (type === "init") {
          workerData.isInitialized = true;
          workerData.initCompletedAt = performance.now();
          if (typeof rest.initDurationMs === "number") {
            workerData.workerInitDurationMs = rest.initDurationMs;
          }
          if (firstReadyAt === null) {
            firstReadyAt = workerData.initCompletedAt;
          }
          if (
            allReadyAt === null &&
            workerPool.length === POOL_SIZE &&
            workerPool.every((w) => w.isInitialized)
          ) {
            allReadyAt = workerData.initCompletedAt;
          }
        }
        resolve(rest);
      }
    }
  });

  worker.addEventListener("error", (error) => {
    console.error("Worker error:", error);
    restartWorker(workerData);
  });

  worker.addEventListener("messageerror", (error) => {
    console.error("Worker message error:", error);
    restartWorker(workerData);
  });
}

function restartWorker(workerData: WorkerData) {
  console.log("Restarting worker due to error");

  // Terminate the old worker
  workerData.worker.terminate();

  // Create new worker
  const newWorker = new PyodideWorker();
  workerData.worker = newWorker;
  workerData.requestCount = 0;
  workerData.activeRequests = 0;
  workerData.isInitialized = false;
  workerData.initPromise = null;
  workerData.initStartedAt = performance.now();
  workerData.initCompletedAt = null;
  workerData.workerInitDurationMs = null;

  // Setup listeners for new worker
  setupWorkerListener(workerData);

  // Initialize new worker
  initializeWorker(workerData);
}

async function initializeWorker(workerData: WorkerData): Promise<void> {
  if (workerData.isInitialized) return;
  if (workerData.initPromise) return workerData.initPromise;

  workerData.initStartedAt = performance.now();
  workerData.initPromise = new Promise<void>((resolve, reject) => {
    const id = getId();

    pending.set(id, {
      resolve: () => {
        resolve();
      },
      reject: (error) => {
        workerData.initPromise = null;
        reject(error);
      },
    });

    workerData.worker.postMessage({ id, type: "init" });
  });

  return workerData.initPromise;
}

// Initialize worker pool
for (let i = 0; i < POOL_SIZE; i++) {
  const workerData = createWorker();
  workerPool.push(workerData);
  // Initialize workers in background
  initializeWorker(workerData).catch((error) => {
    console.error("Failed to initialize worker:", error);
  });
}

// Prefer initialized & idle workers, then least-busy initialized, else round-robin
let rrIndex = 0;
function nextWorker(): WorkerData {
  let selected: WorkerData | undefined;

  // 1. Prefer an initialized, idle worker
  for (let offset = 0; offset < workerPool.length; offset++) {
    const idx = (rrIndex + offset) % workerPool.length;
    const candidate = workerPool[idx];
    if (
      candidate.isInitialized &&
      candidate.activeRequests === 0 &&
      candidate.requestCount < MAX_REQUESTS_PER_WORKER
    ) {
      selected = candidate;
      rrIndex = (idx + 1) % workerPool.length;
      break;
    }
  }

  // 2. Otherwise pick the initialized worker with the fewest active requests
  if (!selected) {
    let bestActive = Infinity;
    for (let offset = 0; offset < workerPool.length; offset++) {
      const idx = (rrIndex + offset) % workerPool.length;
      const candidate = workerPool[idx];
      if (
        candidate.isInitialized &&
        candidate.requestCount < MAX_REQUESTS_PER_WORKER &&
        candidate.activeRequests < bestActive
      ) {
        bestActive = candidate.activeRequests;
        selected = candidate;
        rrIndex = (idx + 1) % workerPool.length;
      }
    }
  }

  // 3. Fallback to round-robin if none are initialized yet
  if (!selected) {
    selected = workerPool[rrIndex];
    rrIndex = (rrIndex + 1) % workerPool.length;
  }

  // Check if worker needs recycling
  if (selected.requestCount >= MAX_REQUESTS_PER_WORKER) {
    console.log("Recycling worker due to request limit");
    restartWorker(selected);
  }

  return selected;
}

// Send a message with id, resolve when matching response returns
function requestResponse(msg: any) {
  const id = getId();
  const { promise, resolve, reject } = getPromiseAndResolve<any>();

  pending.set(id, { resolve, reject });

  const workerData = nextWorker();
  workerData.activeRequests++;

  // Ensure worker is initialized before sending prediction request
  const sendRequest = async () => {
    try {
      if (!workerData.isInitialized) {
        await initializeWorker(workerData);
      }
      workerData.requestCount++;
      workerData.worker.postMessage({ id, ...msg });
    } catch (error) {
      const pendingData = pending.get(id);
      if (pendingData) {
        pending.delete(id);
        reject(error);
      }
    }
  };

  sendRequest();
  return promise.finally(() => {
    workerData.activeRequests = Math.max(0, workerData.activeRequests - 1);
  });
}

export function getWorkerPoolMetrics(): WorkerPoolMetrics {
  const initializedCount = workerPool.filter((w) => w.isInitialized).length;
  return {
    poolSize: workerPool.length,
    initializedCount,
    allReady: initializedCount === workerPool.length,
    poolCreatedAt,
    firstReadyAt,
    allReadyAt,
    workers: workerPool.map((w, index) => ({
      index,
      isInitialized: w.isInitialized,
      activeRequests: w.activeRequests,
      requestCount: w.requestCount,
      wallInitMs:
        w.initCompletedAt !== null ? w.initCompletedAt - w.initStartedAt : null,
      workerInitDurationMs: w.workerInitDurationMs,
    })),
  };
}

export async function whenPoolReady(): Promise<WorkerPoolMetrics> {
  await Promise.all(workerPool.map((w) => initializeWorker(w)));
  return getWorkerPoolMetrics();
}

export async function asyncRun(script: string, context: any) {
  return requestResponse({
    context,
    python: script,
  });
}
