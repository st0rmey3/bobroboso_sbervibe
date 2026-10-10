import { expect, test, type Page } from "@playwright/test";
import type { ApplicationPublic, Country } from "../src/api/types";

// Synthetic fixtures are restricted to browser tests; the UI uses the real API.
const countries: Country[] = [
  {
    code: "RU",
    label: "Россия",
    doc_types: [
      { code: "passport_ru", label: "Паспорт РФ", fields: [] },
      { code: "snils", label: "СНИЛС", fields: [] },
    ],
  },
];

function fixture(): ApplicationPublic {
  return {
    id: "submission-application",
    full_name: "Тестовый Соискатель",
    country: "RU",
    status: "draft",
    doc_set: ["passport_ru", "snils"],
    missing: ["passport_ru", "snils"],
    documents: [],
    slots: countries[0].doc_types.map((type) => ({
      doc_type: type.code,
      label: type.label,
      required: true,
      state: "missing",
      document_ids: [],
      missing_fields: [],
      warnings: [],
    })),
  };
}
function file(name: string) {
  return { name, mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 synthetic browser test only") };
}
async function serve(page: Page, app: ApplicationPublic, onRead?: () => void) {
  await page.addInitScript(({ id }) => localStorage.setItem(`app-token:${id}`, "synthetic-applicant-token"), {
    id: app.id,
  });
  await page.route("**/api/public/countries", (route) => route.fulfill({ json: countries }));
  await page.route(`**/api/public/applications/${app.id}`, (route) => {
    expect(route.request().headers()["x-application-token"]).toBe("synthetic-applicant-token");
    onRead?.();
    return route.fulfill({ json: app });
  });
  await page.goto(`/?a=${app.id}`);
  await expect(page.getByRole("heading", { name: app.full_name, exact: true })).toBeVisible();
}
function addDocument(app: ApplicationPublic, name: string, type: string | null) {
  const doc = {
    id: `file-${app.documents.length}`,
    filename: name,
    declared_type: type,
    status: "queued" as const,
    status_reason: null,
    created_at: "2026-10-10T08:00:00Z",
  };
  app.documents.push(doc);
  app.status = "processing";
  if (type) {
    const slot = app.slots.find((item) => item.doc_type === type)!;
    slot.document_ids.push(doc.id);
    slot.state = "processing";
  } else {
    app.slots.push({
      doc_type: "unknown",
      label: "Нераспознанные файлы",
      required: false,
      state: "processing",
      document_ids: [doc.id],
      missing_fields: [],
      warnings: [],
    });
  }
  return doc;
}

test("one explicit batch submits selected slots and untyped files and shows the detected Belarus passport at 375px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  const app = fixture();
  const requests: string[] = [];
  let resolveUploads!: () => void;
  const uploadGate = new Promise<void>((resolve) => {
    resolveUploads = resolve;
  });
  let readsAfterUpload = 0;
  await page.route(`**/api/public/applications/${app.id}/documents`, async (route) => {
    expect(route.request().headers()["x-application-token"]).toBe("synthetic-applicant-token");
    const body = route.request().postData()!;
    requests.push(body);
    const other = body.includes("belarus.webp");
    if (other) expect(body).not.toContain('name="declared_type"');
    else {
      expect(body).toContain('name="declared_type"');
      expect(body).toContain("passport_ru");
    }
    await uploadGate;
    await route.fulfill({
      status: 202,
      json: addDocument(app, other ? "belarus.webp" : "passport.pdf", other ? null : "passport_ru"),
    });
  });
  await serve(page, app, () => {
    if (!app.documents.length || ++readsAfterUpload < 2) return;
    const unknown = app.slots.find((slot) => slot.doc_type === "unknown");
    if (unknown) {
      unknown.doc_type = "passport_by";
      unknown.label = "Паспорт гражданина Беларуси";
      unknown.state = "ok";
    }
    app.documents.forEach((doc) => {
      doc.status = "done";
    });
  });
  await expect(page.getByRole("button", { name: "Отправить комплект", exact: true })).toBeDisabled();
  await page.getByLabel("Добавить файлы: Паспорт РФ").setInputFiles([file("passport.pdf"), file("remove.pdf")]);
  await page.getByRole("button", { name: "Убрать файл: remove.pdf", exact: true }).click();
  await page.getByLabel("Добавить файлы: Другой документ").setInputFiles({
    name: "belarus.webp",
    mimeType: "image/webp",
    buffer: Buffer.from("RIFF synthetic WEBP browser test only"),
  });
  expect(requests).toHaveLength(0);
  await expect(page.getByText("К отправке: 2.", { exact: false })).toBeVisible();
  await page.screenshot({ path: "test-results/applicant-selected-mobile.png", fullPage: true });
  const submit = page.getByRole("button", { name: "Отправить комплект", exact: true });
  await submit.click();
  await expect(page.getByRole("button", { name: "Отправляем комплект…", exact: true })).toBeDisabled();
  await expect(page.getByLabel("Добавить файлы: Другой документ")).toBeDisabled();
  await expect.poll(() => requests.length).toBe(2);
  await page.getByRole("button", { name: "Отправляем комплект…", exact: true }).dispatchEvent("click");
  resolveUploads();
  const receipt = page.getByRole("status", { name: "Подтверждение приёма" });
  await expect(receipt).toContainText("Номер заявки: submissi. Принято файлов: 2.");
  await expect(receipt).toContainText("Разбор идёт в фоне");
  await expect(page.getByRole("heading", { name: "Паспорт гражданина Беларуси", exact: true })).toBeVisible();
  await expect(page.getByLabel("Выбранные файлы: Другой документ")).toHaveCount(0);
  expect(requests).toHaveLength(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/applicant-submitted-mobile.png", fullPage: true });
});

test("partial batch keeps per-file errors and retries only the refused file", async ({ page }) => {
  const app = fixture();
  const calls: string[] = [];
  let reject = true;
  await page.route(`**/api/public/applications/${app.id}/documents`, (route) => {
    const bad = route.request().postData()!.includes("refused.pdf");
    calls.push(bad ? "refused" : "accepted");
    if (bad && reject)
      return route.fulfill({ status: 503, json: { detail: "Не удалось сохранить файл. Повторите отправку." } });
    return route.fulfill({ status: 202, json: addDocument(app, bad ? "refused.pdf" : "accepted.pdf", "passport_ru") });
  });
  await serve(page, app);
  await page.getByLabel("Добавить файлы: Паспорт РФ").setInputFiles(file("accepted.pdf"));
  await page.getByLabel("Добавить файлы: Паспорт РФ").setInputFiles(file("refused.pdf"));
  await page.getByRole("button", { name: "Отправить комплект", exact: true }).click();
  const receipt = page.getByRole("status", { name: "Подтверждение приёма" });
  await expect(receipt).toContainText("Принято файлов: 1.");
  await expect(receipt).toContainText("Не принято файлов: 1.");
  await expect(page.getByRole("alert")).toHaveText("Не удалось сохранить файл. Повторите отправку.");
  await expect(page.getByLabel("Выбранные файлы: Паспорт РФ").getByRole("listitem")).toHaveCount(1);
  reject = false;
  await page.getByRole("button", { name: "Отправить комплект", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Отправить комплект", exact: true })).toBeDisabled();
  expect(calls.filter((call) => call === "accepted")).toHaveLength(1);
  expect(calls.filter((call) => call === "refused")).toHaveLength(2);
});

test("a wholly refused batch never shows a success receipt and can be removed", async ({ page }) => {
  const app = fixture();
  await page.route(`**/api/public/applications/${app.id}/documents`, (route) =>
    route.fulfill({ status: 409, json: { detail: "Этот файл уже загружен в заявку" } }),
  );
  await serve(page, app);
  await page.getByLabel("Добавить файлы: Другой документ").setInputFiles(file("duplicate.pdf"));
  await page.getByRole("button", { name: "Отправить комплект", exact: true }).click();
  await expect(page.getByText("Комплект не принят.", { exact: false })).toBeVisible();
  await expect(page.getByText("Этот файл уже загружен в заявку", { exact: true })).toBeVisible();
  await expect(page.getByRole("status", { name: "Подтверждение приёма" })).toHaveCount(0);
  await page.getByRole("button", { name: "Убрать файл: duplicate.pdf", exact: true }).click();
  await expect(page.getByRole("button", { name: "Отправить комплект", exact: true })).toBeDisabled();
});

for (const status of ["accepted", "rejected"] as const) {
  test(`a ${status} application offers neither untyped uploads nor batch submission`, async ({ page }) => {
    const app = fixture();
    app.status = status;
    await serve(page, app);
    await expect(page.getByText("Заявка рассмотрена. Загрузка новых файлов закрыта.", { exact: true })).toBeVisible();
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Отправить комплект", exact: true })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Другой документ — определим сами", exact: true })).toHaveCount(0);
  });
}

test("closing an application during submission preserves the untyped file refusal", async ({ page }) => {
  const app = fixture();
  await page.route(`**/api/public/applications/${app.id}/documents`, (route) => {
    app.status = "accepted";
    return route.fulfill({ status: 409, json: { detail: "Заявка уже рассмотрена, загрузка закрыта" } });
  });
  await serve(page, app);
  await page.getByLabel("Добавить файлы: Другой документ").setInputFiles(file("late.pdf"));
  await page.getByRole("button", { name: "Отправить комплект", exact: true }).click();
  await expect(page.getByText("Заявка рассмотрена. Загрузка новых файлов закрыта.", { exact: true })).toBeVisible();
  await expect(page.getByText("Заявка уже рассмотрена, загрузка закрыта", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Выбранные файлы: Другой документ")).toContainText("late.pdf");
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Отправить комплект", exact: true })).toHaveCount(0);
});
