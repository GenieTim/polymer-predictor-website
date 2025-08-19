import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.28.1/full/pyodide.mjs";
import pylimerTools from "../public/pylimer_tools-0.3.4-cp313-cp313-pyodide_2025_0_wasm32.whl?url";

let pyodideReadyPromise = loadPyodide();

self.onmessage = async (event) => {
  // make sure loading is done
  const pyodide = await pyodideReadyPromise;
  const { id, python, context } = event.data;
  // install the packages we need
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");
  // install all the dependencies we have in parallel
  await Promise.all([
    micropip.install("numpy"),
    // micropip.install("scipy"),
    micropip.install("pandas"),
    micropip.install("openpyxl"),
    micropip.install("pint"),
    // some annoying dependencies of pylimer_tools
    micropip.install("click"),
    micropip.install("termcolor"),
    // pylimer_tools
    micropip.install(pylimerTools),
  ]);
  // Now load any packages we need, run the code, and send the result back.
  await pyodide.loadPackagesFromImports(python);
  // make a Python dictionary with the data from `context`
  const dict = pyodide.globals.get("dict");
  const globals = dict(Object.entries(context));
  try {
    // Execute the python code in this context
    let result = await pyodide.runPythonAsync(python, { globals });
    console.log("Webworker with id = " + id + " returned ", result);

    // make sure it's not a pyodide proxy object anymore
    result = JSON.parse(JSON.stringify(result)); 

    self.postMessage({ result, id });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    self.postMessage({ error: errorMessage, id });
  }
};
