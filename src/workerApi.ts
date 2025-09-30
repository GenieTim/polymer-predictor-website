import { v4 as uuidv4 } from "uuid";
import PyodideWorker from "./webworker?worker";

interface WorkerData {
  worker: Worker;
  requestCount: number;
  isInitialized: boolean;
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

function createWorker(): WorkerData {
  const worker = new PyodideWorker();
  const workerData: WorkerData = {
    worker,
    requestCount: 0,
    isInitialized: false,
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
  workerData.isInitialized = false;

  // Setup listeners for new worker
  setupWorkerListener(workerData);

  // Initialize new worker
  initializeWorker(workerData);
}

async function initializeWorker(workerData: WorkerData): Promise<void> {
  if (workerData.isInitialized) return;

  return new Promise((resolve, reject) => {
    const id = getId();

    pending.set(id, {
      resolve: () => {
        resolve();
      },
      reject: (error) => {
        reject(error);
      },
    });

    workerData.worker.postMessage({ id, type: "init" });
  });
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

// Round-robin selection with recycling
let rrIndex = 0;
function nextWorker(): WorkerData {
  const workerData = workerPool[rrIndex];

  // Check if worker needs recycling
  if (workerData.requestCount >= MAX_REQUESTS_PER_WORKER) {
    console.log("Recycling worker due to request limit");
    restartWorker(workerData);
  }

  rrIndex = (rrIndex + 1) % workerPool.length;
  return workerData;
}

// Send a message with id, resolve when matching response returns
function requestResponse(msg: any) {
  const id = getId();
  const { promise, resolve, reject } = getPromiseAndResolve<any>();

  pending.set(id, { resolve, reject });

  const workerData = nextWorker();

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
  return promise;
}

export async function asyncRun(script: string, context: any) {
  return requestResponse({
    context,
    python: script,
  });
}
