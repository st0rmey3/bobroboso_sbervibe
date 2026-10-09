import { userManager } from "../../auth/oidc";

// TODO(T-005): operator workplace — see coord/tasks/T-005-operator-ui.md
// queue (GET /applications, /stats) → application card: original file next to extracted fields,
// low-confidence fields highlighted, inline edit (PATCH /documents/{id}/fields), reprocess, history.
export default function OperatorPage() {
  return (
    <main>
      <h1>Рабочее место оператора</h1>
      <p>Каркас. Реализация — задача T-005.</p>
      <button onClick={() => userManager.signoutRedirect()}>Выйти</button>
    </main>
  );
}
