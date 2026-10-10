import { expect, test, type Page } from "@playwright/test";
import type { ApplicationOperator, ApplicationPublic, Country, DocumentOperator } from "../src/api/types";

// Synthetic API responses exist only in tests. Production always uses the server.
const countries: Country[] = [
  { code: "RU", label: "Россия", doc_types: [
    { code: "passport_ru", label: "Паспорт РФ", fields: [{ name: "series", label: "Серия", required: true }] },
    { code: "snils", label: "СНИЛС", fields: [] }, { code: "inn", label: "ИНН", fields: [] },
  ] },
  { code: "UZ", label: "Узбекистан", doc_types: [
    { code: "passport_uz", label: "Паспорт Узбекистана", fields: [] }, { code: "migration_card", label: "Миграционная карта", fields: [] }, { code: "patent", label: "Патент на работу", fields: [] },
  ] },
  { code: "EU", label: "Европа", doc_types: [{ code: "eu_id", label: "Удостоверение личности ЕС", fields: [] }, { code: "residence_permit", label: "Вид на жительство", fields: [] }] },
];

const publicApp: ApplicationPublic = {
  id: "test-application", full_name: "Тестовый Соискатель", country: "RU", status: "draft", doc_set: ["passport_ru"], missing: ["passport_ru"], documents: [],
  slots: [{ doc_type: "passport_ru", label: "Паспорт РФ", required: true, state: "missing", document_ids: [], missing_fields: [], warnings: [] }],
};

async function catalog(page: Page) {
  await page.route("**/api/public/countries", (route) => route.fulfill({ json: countries }));
}

test("country changes required documents and mobile layout fits 375px", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await catalog(page);
  await page.goto("/");
  const items = page.locator(".checklist-preview li");
  await expect(items).toHaveCount(3);
  await expect(items.first()).toHaveText("Паспорт РФ");
  await page.getByLabel("Гражданство").selectOption("UZ");
  await expect(items).toHaveCount(3);
  await expect(items.first()).toHaveText("Паспорт Узбекистана");
  await page.getByLabel("Гражданство").selectOption("EU");
  await expect(items).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/applicant-mobile.png", fullPage: true });
});

test("create, upload multiple pages, poll, restore and display duplicate refusal", async ({ page }) => {
  await catalog(page);
  const app = structuredClone(publicApp);
  let uploads = 0;
  let reads = 0;
  let duplicate = false;
  await page.route("**/api/public/applications", async (route) => {
    expect(route.request().postDataJSON()).toEqual({ full_name: "Тестовый Соискатель", phone: null, country: "RU" });
    await route.fulfill({ status: 201, json: { id: app.id, token: "synthetic-test-token" } });
  });
  await page.route(`**/api/public/applications/${app.id}`, async (route) => {
    expect(route.request().headers()["x-application-token"]).toBe("synthetic-test-token");
    reads++;
    if (uploads && reads >= 4) { app.documents.forEach((doc) => { doc.status = "done"; }); app.slots[0].state = "ok"; app.status = "ready"; }
    await route.fulfill({ json: app });
  });
  await page.route(`**/api/public/applications/${app.id}/documents`, async (route) => {
    expect(route.request().headers()["x-application-token"]).toBe("synthetic-test-token");
    expect(route.request().postData()).toContain("passport_ru");
    if (duplicate) { await route.fulfill({ status: 409, json: { detail: "Этот файл уже загружен в заявку" } }); return; }
    uploads++;
    const doc = { id: `document-${uploads}`, declared_type: "passport_ru", filename: `page-${uploads}.pdf`, status: "queued" as const, status_reason: null, created_at: "2026-10-10T08:00:00Z" };
    app.documents.push(doc); app.slots[0].document_ids.push(doc.id); app.slots[0].state = "processing"; app.missing = []; app.status = "processing";
    await route.fulfill({ status: 202, json: doc });
  });
  await page.goto("/");
  await page.getByLabel("Фамилия, имя и отчество").fill(app.full_name);
  await page.getByRole("button", { name: "Перейти к загрузке" }).click();
  await expect(page).toHaveURL(/\?a=test-application/);
  const file = (name: string) => ({ name, mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 synthetic test only") });
  await page.getByLabel("Добавить файлы: Паспорт РФ").setInputFiles([file("page-1.pdf"), file("page-2.pdf")]);
  await expect(page.getByText("Принято файлов: 2.", { exact: false })).toBeVisible();
  await expect(page.locator(".file-list .badge-done")).toHaveCount(2, { timeout: 12000 });
  await page.reload();
  await expect(page.getByRole("heading", { name: app.full_name })).toBeVisible();
  await expect(page.locator(".file-list .badge-done")).toHaveCount(2);
  duplicate = true;
  await page.getByLabel("Добавить файлы: Паспорт РФ").setInputFiles(file("page-1.pdf"));
  await expect(page.getByRole("alert")).toContainText("Этот файл уже загружен в заявку");
});

test("missing application token offers recovery and request errors are readable", async ({ page }) => {
  await catalog(page);
  await page.goto("/?a=another-device");
  await expect(page.getByRole("alert")).toContainText("На этом устройстве нет доступа");
  await page.getByRole("link", { name: "Подать новую заявку" }).click();
  await page.route("**/api/public/applications", (route) => route.fulfill({ status: 422, json: { detail: "Укажите фамилию и имя" } }));
  await page.getByLabel("Фамилия, имя и отчество").fill("А");
  await page.getByRole("button", { name: "Перейти к загрузке" }).click();
  await expect(page.getByRole("alert")).toHaveText("Укажите фамилию и имя");
});

const document: DocumentOperator = {
  id: "operator-document", declared_type: "passport_ru", detected_type: "passport_ru", filename: "synthetic-passport.png", status: "done", status_reason: null,
  mime: "image/png", size: 100, ocr_text: "Тестовый текст", created_at: "2026-10-10T08:00:00Z", updated_at: "2026-10-10T08:00:00Z", processing_ms: 1000, llm_meta: {},
  fields: { series: { value: "1234", confidence: 0.4, issues: [], edited_by: null } },
};

async function operatorSession(page: Page) {
  await catalog(page);
  await page.addInitScript(() => sessionStorage.setItem("oidc.user:http://localhost:8080/realms/docs:operator-ui", JSON.stringify({
    access_token: "synthetic-operator-token", token_type: "Bearer", scope: "openid profile", profile: { sub: "test-operator" }, expires_at: Math.floor(Date.now() / 1000) + 3600,
  })));
}

test("operator without a session redirects to Keycloak using PKCE", async ({ page }) => {
  await page.route("**/realms/docs/.well-known/openid-configuration", (route) => route.fulfill({ json: {
    issuer: "http://localhost:8080/realms/docs", authorization_endpoint: "http://localhost:8080/realms/docs/protocol/openid-connect/auth", token_endpoint: "http://localhost:8080/realms/docs/protocol/openid-connect/token",
  } }));
  await page.route("**/realms/docs/protocol/openid-connect/auth?*", (route) => route.fulfill({ contentType: "text/html", body: "<h1>Вход для оператора</h1>" }));
  await page.goto("/operator/applications/test-application");
  await expect(page).toHaveURL(/localhost:8080\/realms\/docs\/protocol\/openid-connect\/auth/);
  const url = new URL(page.url());
  expect(url.searchParams.get("client_id")).toBe("operator-ui");
  expect(url.searchParams.get("code_challenge_method")).toBe("S256");
  expect(url.searchParams.get("redirect_uri")).toBe("http://localhost:5173/operator/callback");
});

test("operator compares original, saves to source document and requests reprocessing", async ({ page }) => {
  await operatorSession(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  const doc = structuredClone(document);
  const app: ApplicationOperator = { ...structuredClone(publicApp), phone: null, created_at: doc.created_at, status: "ready", missing: [], documents: [doc], history: [], slots: [{ ...publicApp.slots[0], state: "ok", document_ids: [doc.id], fields: { series: { ...doc.fields.series, document_id: doc.id } } }] };
  await page.route(`**/api/operator/applications/${app.id}`, async (route) => { expect(route.request().headers().authorization).toBe("Bearer synthetic-operator-token"); await route.fulfill({ json: app }); });
  await page.route(`**/api/operator/documents/${doc.id}/file`, async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer synthetic-operator-token");
    await route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jh0kAAAAASUVORK5CYII=", "base64") });
  });
  await page.route(`**/api/operator/documents/${doc.id}/fields`, async (route) => {
    expect(route.request().method()).toBe("PATCH");
    expect(route.request().postDataJSON()).toEqual({ fields: { series: "5678" } });
    doc.fields.series = { value: "5678", confidence: 1, issues: [], edited_by: "test-operator" };
    app.slots[0].fields.series = { ...doc.fields.series, document_id: doc.id };
    await route.fulfill({ json: doc });
  });
  await page.route(`**/api/operator/documents/${doc.id}/reprocess`, async (route) => { expect(route.request().method()).toBe("POST"); doc.status = "queued"; app.slots[0].state = "processing"; await route.fulfill({ json: doc }); });
  await page.goto(`/operator/applications/${app.id}`);
  await expect(page.getByRole("img", { name: `Оригинал: ${doc.filename}` })).toBeVisible();
  await expect(page.locator(".field-attention")).toHaveCount(1);
  await page.getByLabel("Серия", { exact: true }).fill("5678");
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  await expect(page.getByText("Правка оператора: test-operator")).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Серия", { exact: true })).toHaveValue("5678");
  await page.screenshot({ path: "test-results/operator-card.png", fullPage: true });
  await page.getByRole("button", { name: "Разобрать заново" }).click();
  await expect(page.locator(".original-file .badge-queued")).toBeVisible();
  await expect(page.getByLabel("Серия", { exact: true })).toBeDisabled();
});

test("operator filters and queue show values returned by API", async ({ page }) => {
  await operatorSession(page);
  await page.route("**/api/operator/applications*", async (route) => {
    const url = new URL(route.request().url());
    await route.fulfill({ json: url.searchParams.has("q") ? [] : [{ id: publicApp.id, full_name: publicApp.full_name, country: "RU", status: "needs_review", documents_total: 3, documents_done: 1, documents_attention: 2, created_at: document.created_at, updated_at: document.updated_at }] });
  });
  await page.route("**/api/operator/stats", (route) => route.fulfill({ json: { queued: 7, running: 2, done: 9, failed: 1, avg_processing_ms: 1400 } }));
  await page.route("**/api/operator/processing", (route) => route.fulfill({ json: [{ document_id: document.id, application_id: publicApp.id, full_name: publicApp.full_name, filename: document.filename, status: "recognizing", attempts: 2, last_error: null, created_at: document.created_at, updated_at: document.updated_at }] }));
  await page.goto("/operator");
  await expect(page.getByRole("link", { name: publicApp.full_name })).toBeVisible();
  await page.getByLabel("Поиск по имени").fill("Никого");
  await page.getByRole("button", { name: "Найти", exact: true }).click();
  await expect(page.getByText("Заявок по выбранным условиям пока нет.")).toBeVisible();
  await page.getByRole("link", { name: "В работе", exact: true }).click();
  await expect(page.locator(".stat").filter({ hasText: "Ждут разбора" }).locator("strong")).toHaveText("7");
  await expect(page.getByText(document.filename, { exact: true })).toBeVisible();
  await expect(page.getByText("Распознавание текста", { exact: true })).toBeVisible();
});
