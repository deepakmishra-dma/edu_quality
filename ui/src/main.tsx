import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import "./index.css";

// The app is served from /ui/<path>, so routes are declared without that prefix.
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename="/ui">
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
