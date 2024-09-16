import {Route, Routes} from "react-router-dom";
import {Authenticated, useIsAuthenticated} from "@refinedev/core";
import {Login} from "./login";
import {Header} from "../components";
import {NoticeList} from "./notices";
import {NoticeDetails} from "./notices/details.tsx";
import {ErrorComponent} from "@refinedev/mantine";
import {AppShell} from "@mantine/core";

const Pages = () => {
  const isAuthenticated = useIsAuthenticated()
  return (
    <AppShell sx={{
      "display": "flex",
      "flex-direction": "column",
      "justify-content": "center",
      "align-items": "center",
      ".mantine-AppShell-body": {
        "max-width": "700px",
        "width": "100%",
        "box-shadow": "0 0 10px 10px rgba(0, 0, 0, 0.1)",
        "padding": isAuthenticated.data?.authenticated ? "0" : "0",
        ".mantine-AppShell-main": {
          "padding-left": isAuthenticated.data?.authenticated ? "5px" : "0",
          "padding-right": isAuthenticated.data?.authenticated ? "5px" : "0",
          "padding-bottom": isAuthenticated.data?.authenticated ? "5px" : "0",
          "padding-top": isAuthenticated.data?.authenticated ? undefined : "0",
          "position": "relative",
          "width": '100%'
        }
      }
    }}>
      <Routes>
        <Route path="/*" element={
          <Authenticated
            key="authenticated-outer"
            fallback={<Login/>}
            v3LegacyAuthProviderCompatible
          >
            <Header/>
            <Routes>
              <Route path="/" element={<NoticeList/>}/>
              <Route path="/notice/:id" element={<NoticeDetails/>}/>
              <Route path="*" element={<ErrorComponent/>}/>
            </Routes>
          </Authenticated>
        }/>
      </Routes>
    </AppShell>
  );
};

export default Pages;
