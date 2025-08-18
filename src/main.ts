import { mount } from "svelte";
import "./app.css";
// Import Halfmoon CSS
import "halfmoon/css/halfmoon.min.css";
import "./color-mode-toggle";
//
import App from "./App.svelte";
import Home from "./Home.svelte";
import NotFound from "./NotFound.svelte";

const currentRoute = window.location.pathname;
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
