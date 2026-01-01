import { Route, Routes, useNavigate } from "react-router-dom";
import { Authenticated, useIsAuthenticated } from "@refinedev/core";
import { Login } from "./login.tsx";
import { Header } from "../components";
import { NoticeList } from "./notices";
import { NoticeDetails } from "./notices/details.tsx";
import { ErrorComponent } from "@refinedev/mantine";
import { AppShell } from "@mantine/core";
import Navbar from "../components/organisms/navbar";
import React, { useEffect } from "react";
import Cmap from "./cmap";
import CmapList from "./cmap/list.tsx";
import LeaveNote from "./leave-note.tsx";
import { SchoolCalendar } from "./SchoolCalendar.tsx";
import { BonafideCertificate } from "./BonafideCertificate.tsx";
import PortionCircular from "./portion-circular/index.tsx";
import PortionCircularList from "./portion-circular/list.tsx";
import DateCmap from "./date-circular/index.tsx";
import CmapDateList from "./date-circular/list.tsx";
import EarlyPickup from "./EarlyPickup.tsx";

import { StudentProfle } from "./StudentProfile.tsx";
import { PtmLinks } from "./PtmLinks.tsx";
import { Fee } from "./Fee.tsx";
import { Results } from "./Results.tsx";
// import { Results } from "./Result.tsx";

const Pages = () => {
  // const location = useLocation()
  const isAuthenticated = useIsAuthenticated();
  const [isNavBarOpen, setIsNavBarOpen] = React.useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    // @ts-expect-error new assignment
    window.updateLocation = navigate;
  }, [navigate]);
  return (
    <AppShell
      sx={{
        display: "flex",
        "flex-direction": "column",
        "justify-content": "center",
        "align-items": "center",
        ".mantine-AppShell-body": {
          "max-width": "700px",
          width: "100%",
          "box-shadow": "0 0 10px 10px rgba(0, 0, 0, 0.1)",
          padding: isAuthenticated.data?.authenticated ? "0" : "0",
          ".mantine-AppShell-main": {
            "padding-left": isAuthenticated.data?.authenticated ? "0px" : "0",
            "padding-right": isAuthenticated.data?.authenticated ? "0px" : "0",
            "padding-bottom": isAuthenticated.data?.authenticated ? "5px" : "0",
            "padding-top": isAuthenticated.data?.authenticated ? "60px" : "0",
            position: "relative",
            width: "100%",
          },
        },
      }}
    >
      <Routes>
        <Route
          path="/*"
          element={
            <Authenticated
              key="authenticated-outer"
              fallback={<Login />}
              v3LegacyAuthProviderCompatible
            >
              <Header
                setNavbarOpen={setIsNavBarOpen}
                navbarOpen={isNavBarOpen}
              />
              <Navbar isOpen={isNavBarOpen} setIsOpen={setIsNavBarOpen} />
              <Routes>
                <Route path="/" element={<NoticeList />} />
                <Route path="/stared" element={<NoticeList staredOnly />} />
                <Route path="/archived" element={<NoticeList archivedOnly />} />
                <Route path="/calendar" element={<SchoolCalendar />} />
                <Route path="/bonafide" element={<BonafideCertificate />} />
                <Route path="/ptm-link" element={<PtmLinks />} />
                <Route path="/student-profile" element={<StudentProfle />} />
                <Route path="/early-pickup" element={<EarlyPickup />} />
                <Route path="/notice/:id" element={<NoticeDetails />} />
                <Route path="/cmap" element={<Cmap />} />
                <Route path="/cmap/list" element={<CmapList />} />
                <Route path="/portion-circular" element={<PortionCircular />} />
                <Route path="/fee" element={<Fee />} />
                <Route path="/result" element={<Results />} />
                <Route
                  path="/portion-circular/list"
                  element={<PortionCircularList />}
                />

                <Route path="/date-circular" element={<DateCmap />} />
                <Route path="/date-circular/list" element={<CmapDateList />} />
                <Route path="/leave-note" element={<LeaveNote />} />
                <Route path="*" element={<ErrorComponent />} />
              </Routes>
            </Authenticated>
          }
        />
      </Routes>
    </AppShell>
  );
};

export default Pages;
