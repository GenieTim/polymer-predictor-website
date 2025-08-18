import "./style.css";
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.28.1/full/pyodide.mjs";

let pyodide;

async function setup_python() {
  pyodide = await loadPyodide({});

  await pyodide.loadPackage("micropip", {
    checkIntegrity: false,
  });
  const micropip = pyodide.pyimport("micropip");
  // install all the dependencies we have
  await micropip.install("numpy");
  await micropip.install("pandas");
  await micropip.install("pint");
  await micropip.install(
    "/pylimer_tools-0.3.3-cp313-cp313-pyodide_2025_0_wasm32.whl"
  );

  return pyodide.runPythonAsync(`
import pylimer_tools
pylimer_tools.__version__
  `);
}

setup_python().then((result) => {
  console.log("Python says that pylimer_tools_version = ", result);
});
