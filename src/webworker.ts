// @ts-expect-error - Pyodide is loaded from CDN without type declarations
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

let pyodideReadyPromise = loadPyodide();
let isInitialized = false;
let initializationPromise: Promise<void> | null = null;
let initDurationMs: number | null = null;

async function initializeWorker(pyodide: any) {
  if (isInitialized) return;
  
  // Prevent multiple initialization attempts
  if (initializationPromise) {
    await initializationPromise;
    return;
  }

  initializationPromise = (async () => {
    const start = performance.now();
    try {
      // Install micropip and numpy first (numpy has native .so extensions that
      // must finish dynamic linking before other native wheels are loaded)
      await pyodide.loadPackage(["micropip", "numpy"]);
      const micropip = pyodide.pyimport("micropip");

      // Install remaining dependencies
      await micropip.install([
        "pint",
        "click",
        "termcolor",
        "pylimer-tools>=0.6.0",
      ]);

      // Pre-import core modules and C++ extensions during background warmup
      // so the first prediction does not pay dlopen/import latency.
      await pyodide.runPythonAsync(
        "import math, warnings, numpy, pint, pylimer_tools, pylimer_tools_cpp"
      );
      
      isInitialized = true;
      initDurationMs = performance.now() - start;
      console.log(
        `Worker initialized successfully in ${initDurationMs.toFixed(0)} ms`
      );
    } catch (error) {
      initializationPromise = null;
      console.error("Worker initialization failed:", error);
      throw error;
    }
  })();

  await initializationPromise;
}

self.onmessage = async (event) => {
  const { id, python, context, type, loadImports } = event.data;
  
  try {
    // Handle initialization request
    if (type === "init") {
      const pyodide = await pyodideReadyPromise;
      await initializeWorker(pyodide);
      self.postMessage({ id, type: "init", success: true, initDurationMs });
      return;
    }

    // Handle prediction request
    const pyodide = await pyodideReadyPromise;
    await initializeWorker(pyodide);
    
    // Only scan imports when explicitly requested; standard worker scripts
    // only use packages pre-loaded in initializeWorker.
    if (loadImports) {
      await pyodide.loadPackagesFromImports(python);
    }
    
    // Create Python dictionary with the data from context
    const dict = pyodide.globals.get("dict");
    const globals = dict(Object.entries(context || {}));
    
    // Execute the python code in this context
    let result = await pyodide.runPythonAsync(python, { globals });
    console.log("Webworker with id = " + id + " returned ", result);

    // Ensure it's not a pyodide proxy object anymore
    result = JSON.parse(JSON.stringify(result)); 

    self.postMessage({ result, id });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Worker error:", errorMessage);
    self.postMessage({ error: errorMessage, id });
  }
};
