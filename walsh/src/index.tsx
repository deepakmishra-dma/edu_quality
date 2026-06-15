import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./i18n";
import { QueryClient, QueryClientProvider } from "react-query";

const container = document.getElementById("root") as HTMLElement;
const root = createRoot(container);

const queryClient = new QueryClient();

root.render(
  <React.StrictMode>
    <React.Suspense fallback="loading">
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.Suspense>
  </React.StrictMode>
);
