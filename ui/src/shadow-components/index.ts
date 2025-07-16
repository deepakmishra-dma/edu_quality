import React from "react";
import ReactDOM from "react-dom/client";
import CreateExamComponent from "./create-exam-component";

import r2wc from "react-to-webcomponent";

customElements.define(
  "create-exam-table",
  r2wc(CreateExamComponent, React, ReactDOM)
);
