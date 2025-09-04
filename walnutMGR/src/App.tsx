// import { Index } from "./components/pages/index.js"
import { Refine } from "@refinedev/core";
import dataProvider from "@refinedev/simple-rest";
import routerProvider from "@refinedev/react-router-v6";
import { BrowserRouter, Routes, Route } from "react-router-dom";


import { IDataMultipleContextProvider } from "@refinedev/core/dist/contexts/data/IDataContext";

import { Index } from "./components/pages";




// import DragTest from "./D "

const provider: IDataMultipleContextProvider = {
	default: dataProvider(window.location.origin + "/api/resource"),
}



function App() {
	return (
		<div >
			<BrowserRouter>
				<Refine dataProvider={provider}
					routerProvider={routerProvider}>

					<Routes>
						<Route path="/" element={<Index />} />

					</Routes>
				</Refine>
			</BrowserRouter>
		</div>
	)
}

export default App
