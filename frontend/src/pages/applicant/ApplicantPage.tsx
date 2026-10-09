// TODO(T-004): applicant flow — see coord/tasks/T-004-applicant-ui.md
// 1) GET /api/public/doc-types → choose document set → POST /applications (store token)
// 2) upload per slot (POST /applications/{id}/documents, multipart) → show server errors as is
// 3) poll GET /applications/{id} every 2 s → statuses, reasons, `missing` list ("дошлите …")
export default function ApplicantPage() {
  return (
    <main>
      <h1>Подача документов</h1>
      <p>Каркас. Реализация — задача T-004.</p>
    </main>
  );
}
