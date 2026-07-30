import { FrappeProvider } from "frappe-react-sdk";
import { Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CreateExamComponent from "./shadow-components/create-exam-component";
import Dashboard from "@/pages/Dashboard/index";
import DashboardHome from "@/pages/Dashboard/home";
import DashboardDetailed from "@/pages/Dashboard/detailed";

const queryClient = new QueryClient();

function App() {
  return (
    <div className="App">
      <FrappeProvider>
        <QueryClientProvider client={queryClient}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />}>
              <Route index element={<DashboardHome />} />
              <Route path="detailed" element={<DashboardDetailed />} />
            </Route>
            <Route path="*" element={<CreateExamComponent />} />
          </Routes>
        </QueryClientProvider>
      </FrappeProvider>
    </div>
  );
}

export default App;
