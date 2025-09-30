import { mount } from "svelte";
import "./app.css";
// Import Halfmoon CSS
import "halfmoon/css/halfmoon.min.css";
import "./color-mode-toggle";
//
import App from "./App.svelte";
import Home from "./Home.svelte";
import NotFound from "./NotFound.svelte";

// Get the base path from Vite's configuration
const basePath = import.meta.env.BASE_URL;

// Get current route - check hash first (for GitHub Pages redirects), then pathname
let currentRoute = '/';

if (window.location.hash.startsWith('#/')) {
  // Hash-based routing (from GitHub Pages 404 redirect)
  currentRoute = window.location.hash.slice(1);
} else {
  // Regular path-based routing
  const fullPath = window.location.pathname;
  currentRoute = fullPath.startsWith(basePath) 
    ? fullPath.slice(basePath.length - 1) 
    : fullPath;
}

// Ensure route starts with /
if (!currentRoute.startsWith('/')) {
  currentRoute = '/' + currentRoute;
}

let app = null;

switch (currentRoute) {
  case "/":
    app = mount(Home, {
      target: document.getElementById("app")!,
    });
    break;
  case "/predictor":
    app = mount(App, {
      target: document.getElementById("app")!,
    });
    break;

  default:
    app = mount(NotFound, {
      target: document.getElementById("app")!,
    });
}

export default app;
