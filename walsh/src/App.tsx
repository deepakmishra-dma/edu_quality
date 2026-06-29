import { Refine } from "@refinedev/core";
import { DevtoolsProvider } from "@refinedev/devtools";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";

import { useNotificationProvider } from "@refinedev/mantine";

import {
  ColorScheme,
  ColorSchemeProvider,
  Global,
  MantineProvider,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { NotificationsProvider } from "@mantine/notifications";
import routerBindings, {
  DocumentTitleHandler,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import { useTranslation } from "react-i18next";
import { BrowserRouter } from "react-router-dom";
import { authProvider } from "./providers/auth";
import "./index.css";
import theme from "./config/theme.ts";
import provider from "./providers/data";
import Pages from "./pages/pages.tsx";
import { QueryClient, QueryClientProvider } from "react-query";

const queryClient = new QueryClient();

function App() {
  const notificationProvider = useNotificationProvider();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
    key: "mantine-color-scheme",
    defaultValue: "light",
    getInitialValueInEffect: true,
  });
  const { t, i18n } = useTranslation();

  const toggleColorScheme = (value?: ColorScheme) =>
    setColorScheme(value || (colorScheme === "dark" ? "light" : "dark"));

  const i18nProvider = {
    translate: (key: string, params: object) => t(key, params),
    changeLocale: (lang: string) => i18n.changeLanguage(lang),
    getLocale: () => i18n.language,
  };

  const cachedData = queryClient.getQueryData('student');
  console.log(cachedData);

  return (
    <BrowserRouter basename="/walsh">
      <QueryClientProvider client={queryClient}>
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
              <Global styles={{ body: { WebkitFontSmoothing: "auto" } }} />
              <NotificationsProvider position="top-right">
                <DevtoolsProvider>
                  <Refine
                    dataProvider={provider}
                    notificationProvider={notificationProvider}
                    routerProvider={routerBindings}
                    authProvider={authProvider}
                    i18nProvider={i18nProvider}
                    resources={[
                      {
                        name: "School Notice",
                        list: "/",
                        show: "/notice/:id",
                        meta: {
                          dataProviderName: "notices",
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
                    <Pages />
                    <RefineKbar />
                    <UnsavedChangesNotifier />
                    <DocumentTitleHandler />
                  </Refine>
                </DevtoolsProvider>
              </NotificationsProvider>
            </MantineProvider>
          </ColorSchemeProvider>
        </RefineKbarProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}

export default App;
