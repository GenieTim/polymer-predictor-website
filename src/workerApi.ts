import { v4 as uuidv4 } from "uuid";
import PyodideWorker from "./webworker?worker";

function getPromiseAndResolve<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function getId() {
  return uuidv4();
}

const POOL_SIZE =
  Math.max(1, (typeof navigator !== "undefined" && (navigator as any).hardwareConcurrency) || 2);
const pyodideWorkers: Worker[] = Array.from({ length: POOL_SIZE }, () => new PyodideWorker());

// Track pending request resolvers by id.
const pending = new Map<string, (value: any) => void>();

// Attach listeners once per worker.
for (const worker of pyodideWorkers) {
  worker.addEventListener("message", (event) => {
    const data = event.data;
    if (!data || typeof data !== "object") return;
    const { id, ...rest } = data;

    if (id && pending.has(id)) {
      const resolve = pending.get(id)!;
      pending.delete(id);
      resolve(rest);
    }
  });
}

// Round-robin selection.
let rrIndex = 0;
function nextWorker(): Worker {
  const w = pyodideWorkers[rrIndex];
  rrIndex = (rrIndex + 1) % pyodideWorkers.length;
  return w;
}

// Send a message with id, resolve when matching response returns.
function requestResponse(msg: any) {
  const idWorker = getId();
  const { promise, resolve } = getPromiseAndResolve<any>();
  pending.set(idWorker, resolve);
  const worker = nextWorker();
  worker.postMessage({ id: idWorker, ...msg });
  return promise;
}

export async function asyncRun(script: string, context: any) {
  return requestResponse({
    context,
    python: script,
  });
}
