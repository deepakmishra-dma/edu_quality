import {Authenticated, Refine} from "@refinedev/core";
import {DevtoolsProvider} from "@refinedev/devtools";
import {RefineKbar, RefineKbarProvider} from "@refinedev/kbar";

import {notificationProvider,} from "@refinedev/mantine";

import {ColorScheme, ColorSchemeProvider, Global, MantineProvider,} from "@mantine/core";
import {useLocalStorage} from "@mantine/hooks";
import {NotificationsProvider} from "@mantine/notifications";
import routerBindings, {
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import dataProvider from "@refinedev/simple-rest";
import {useTranslation} from "react-i18next";
import {BrowserRouter, Outlet, Route, Routes, useLocation} from "react-router-dom";
import {authProvider} from "./providers/auth";
import {Header} from "./components";
import {Login} from "./pages/login";
import "./index.css";
import {BaseLayout} from "./components/layouts/BaseLayout";
import {OtpPage} from "./pages/login/otp";
import theme from "./config/theme.ts";

const TempError = () => {
  const location = useLocation()
  console.log({location})
  return <>
    error
  </>
};

function App() {
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
    key: "mantine-color-scheme",
    defaultValue: "light",
    getInitialValueInEffect: true,
  });
  const {t, i18n} = useTranslation();

  const toggleColorScheme = (value?: ColorScheme) =>
    setColorScheme(value || (colorScheme === "dark" ? "light" : "dark"));

  const i18nProvider = {
    translate: (key: string, params: object) => t(key, params),
    changeLocale: (lang: string) => i18n.changeLanguage(lang),
    getLocale: () => i18n.language,
  };

  return (
    <BrowserRouter basename="/walsh">
      <RefineKbarProvider>
        <ColorSchemeProvider
          colorScheme={colorScheme}
          toggleColorScheme={toggleColorScheme}
        >
          {/* You can change the theme colors here. example: theme={{ ...RefineThemes.Magenta, colorScheme:colorScheme }} */}
          <MantineProvider
            theme={theme(colorScheme)}
            withNormalizeCSS
            withGlobalStyles
          >
            <Global styles={{body: {WebkitFontSmoothing: "auto"}}}/>
            <NotificationsProvider position="top-right">
              <DevtoolsProvider>
                <Refine
                  dataProvider={dataProvider(
                    window.location.href
                  )}
                  notificationProvider={notificationProvider}
                  routerProvider={routerBindings}
                  authProvider={authProvider}
                  i18nProvider={i18nProvider}
                  resources={[
                    {
                      name: "notice-board",
                      list: "/notice-board",
                      show: "/notice-board/:id",
                    },
                    {
                      name: "notice-boardx",
                      list: "/notice-boardx",
                      create: "/notice-boardx/create",
                      edit: "/notice-boardx/edit/:id",
                      show: "/notice-boardx/show/:id",
                      meta: {
                        canDelete: true,
                      },
                    },
                    {
                      name: "categories",
                      list: "/categories",
                      create: "/categories/create",
                      edit: "/categories/edit/:id",
                      show: "/categories/show/:id",
                      meta: {
                        canDelete: true,
                      },
                    },
                  ]}
                  options={{
                    syncWithLocation: true,
                    warnWhenUnsavedChanges: true,
                    useNewQueryKeys: true,
                    projectId: "QlcuD4-yeUftx-Pd8nc4",
                  }}
                >
                  <Routes>
                    <Route
                      element={
                        <div>
                          <Header/>
                          <Outlet/>
                        </div>
                      }
                    >
                      <Route path="*" element={<TempError/>}/>
                    </Route>
                    <Route
                      element={
                        <Authenticated
                          key="authenticated-outer"
                          fallback={<Outlet/>}
                          v3LegacyAuthProviderCompatible
                        >
                          <NavigateToResource/>
                        </Authenticated>
                      }
                    >
                      <Route
                        index
                        element={<NavigateToResource resource="login"/>}
                      />
                      <Route path="/login" element={<Login/>}/>
                      <Route
                        path="/otp"
                        element={
                          <BaseLayout name={"Enter OTP"}>
                            <OtpPage/>
                          </BaseLayout>
                        }
                      />
                    </Route>
                    <Route
                      path="/select-student"
                      element={
                        <BaseLayout name={"Options"}>
                          <Outlet/>
                        </BaseLayout>
                      }
                    />
                  </Routes>
                  <RefineKbar/>
                  <UnsavedChangesNotifier/>
                  <DocumentTitleHandler/>
                </Refine>
                {/* <DevtoolsPanel /> */}
              </DevtoolsProvider>
            </NotificationsProvider>
          </MantineProvider>
        </ColorSchemeProvider>
      </RefineKbarProvider>
    </BrowserRouter>
  );
}

export default App;
