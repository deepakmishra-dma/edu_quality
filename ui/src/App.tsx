import { FrappeProvider } from "frappe-react-sdk";
import CreateExamComponent from "./shadow-components/create-exam-component";
function App() {
  return (
    <div className="App">
      <FrappeProvider>
        <div>
          <CreateExamComponent />
        </div>
      </FrappeProvider>
    </div>
  );
}

export default App;
