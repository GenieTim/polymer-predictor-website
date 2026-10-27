// @ts-expect-error - Pyodide is loaded from CDN without type declarations
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

let pyodideReadyPromise = loadPyodide();
let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

async function initializeWorker(pyodide: any) {
  if (isInitialized) return;
  
  // Prevent multiple initialization attempts
  if (initializationPromise) {
    await initializationPromise;
    return;
  }

  initializationPromise = (async () => {
    try {
      // Install micropip first
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip");
      
      // Install all dependencies in parallel
      await Promise.all([
        micropip.install("numpy"),
        micropip.install("pint"),
        micropip.install("click"),
        micropip.install("termcolor"),
        micropip.install("pylimer-tools"),
      ]);
      
      isInitialized = true;
      console.log("Worker initialized successfully");
    } catch (error) {
      console.error("Worker initialization failed:", error);
      throw error;
    }
  })();

  await initializationPromise;
}

self.onmessage = async (event) => {
  const { id, python, context, type } = event.data;
  
  try {
    // Handle initialization request
    if (type === "init") {
      const pyodide = await pyodideReadyPromise;
      await initializeWorker(pyodide);
      self.postMessage({ id, type: "init", success: true });
      return;
    }

    // Handle prediction request
    const pyodide = await pyodideReadyPromise;
    await initializeWorker(pyodide);
    
    // Load any additional packages needed for this specific script
    await pyodide.loadPackagesFromImports(python);
    
    // Create Python dictionary with the data from context
    const dict = pyodide.globals.get("dict");
    const globals = dict(Object.entries(context));
    
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
