import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.js";
import "./index.css";
import reactToWebComponent from "react-to-webcomponent";

// import { Index } from "./components/pages/index.js";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

customElements.define(
  "cmap-creation-tool",
  reactToWebComponent(App, React, ReactDOM)
);
