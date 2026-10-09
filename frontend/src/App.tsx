import { Route, Routes } from "react-router-dom";
import ApplicantPage from "./pages/applicant/ApplicantPage";
import OperatorCallback from "./pages/operator/OperatorCallback";
import OperatorPage from "./pages/operator/OperatorPage";
import RequireOperator from "./auth/RequireOperator";

// Two separate interfaces in one SPA: applicant at "/", operator workplace at "/operator" (behind Keycloak login).
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ApplicantPage />} />
      <Route path="/operator/callback" element={<OperatorCallback />} />
      <Route
        path="/operator/*"
        element={
          <RequireOperator>
            <OperatorPage />
          </RequireOperator>
        }
      />
    </Routes>
  );
}
