import {Route, Routes} from "react-router-dom";
import {Authenticated, useIsAuthenticated} from "@refinedev/core";
import {Login} from "./login";
import {Header} from "../components";
import {NoticeList} from "./notices";
import {NoticeDetails} from "./notices/details.tsx";
import {ErrorComponent} from "@refinedev/mantine";
import {AppShell} from "@mantine/core";
import Navbar from "../components/organisms/navbar";
import React from "react";

const Pages = () => {
  // const location = useLocation()
  const isAuthenticated = useIsAuthenticated()
  const [isNavBarOpen, setIsNavBarOpen] = React.useState(false)
  // const navBarIsOpen = isNavBarOpen && location.pathname == '/'
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
          "padding-left": isAuthenticated.data?.authenticated ? "0px" : "0",
          "padding-right": isAuthenticated.data?.authenticated ? "0px" : "0",
          "padding-bottom": isAuthenticated.data?.authenticated ? "5px" : "0",
          "padding-top": isAuthenticated.data?.authenticated ? "60px" : "0",
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
            <Header setNavbarOpen={setIsNavBarOpen} navbarOpen={isNavBarOpen}/>
            <Navbar isOpen={isNavBarOpen} setIsOpen={setIsNavBarOpen}/>
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
