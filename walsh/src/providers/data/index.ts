import dataProvider from "@refinedev/simple-rest";
import noticesDataProvider from "./notices.ts";
import {IDataMultipleContextProvider} from "@refinedev/core/dist/contexts/data/IDataContext";


const provider: IDataMultipleContextProvider = {
  default: dataProvider(window.location.origin + "/api/resource"),
  notices: noticesDataProvider
}

export default provider
