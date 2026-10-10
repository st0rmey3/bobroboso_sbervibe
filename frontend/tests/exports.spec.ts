import { readFile } from "node:fs/promises";
import { expect, test, type Download, type Page, type Route } from "@playwright/test";
import type { ApplicationOperator, ExpiringItem } from "../src/api/types";
import { seedOperatorSession } from "./session";

const cardCsv = Buffer.from(
  "\uFEFFДокумент;Поле;Значение;Источник;Уверенность;Замечания\r\nСоискатель;ФИО;Тестовый Соискатель;соискатель;;\r\n",
  "utf8",
);
const listCsv = Buffer.from(
  "\uFEFFЗаявитель;Документ;Поле;Дата;Дней осталось\r\nТестовый Соискатель;Паспорт Беларуси;Срок действия;01.10.2026;'-9\r\n",
  "utf8",
);

function assertAuthenticated(route: Route) {
  expect(route.request().headers().authorization).toBe("Bearer synthetic-operator-token");
  expect(route.request().url()).not.toContain("synthetic-operator-token");
}

async function bytes(download: Download) {
  const file = await download.path();
  expect(file).not.toBeNull();
  return readFile(file!);
}

function cardFixture(): ApplicationOperator {
  return {
    id: "export-application",
    full_name: "Тестовый Соискатель",
    phone: null,
    country: "RU",
    status: "ready",
    created_at: "2026-10-10T08:00:00Z",
    doc_set: ["passport_by"],
    missing: [],
    documents: [
      {
        id: "export-document",
        declared_type: "passport_by",
        detected_type: "passport_by",
        filename: "synthetic.png",
        mime: "image/png",
        size: 100,
        status: "done",
        status_reason: null,
        created_at: "2026-10-10T08:00:00Z",
        updated_at: "2026-10-10T08:00:00Z",
        processing_ms: 1000,
        ocr_text: null,
        llm_meta: {},
        fields: {},
      },
    ],
    slots: [
      {
        doc_type: "passport_by",
        label: "Паспорт Беларуси",
        required: true,
        state: "ok",
        document_ids: ["export-document"],
        missing_fields: [],
        warnings: [],
        fields: {
          number: { label: "Номер", value: "TEST123", confidence: 1, issues: [], document_id: "export-document" },
          full_name: {
            label: "ФИО",
            value: "Тестовый Соискатель",
            confidence: 1,
            issues: [],
            document_id: "export-document",
          },
        },
      },
    ],
    history: [
      {
        actor: "operator:test-operator",
        action: "fields_edited",
        document_id: "export-document",
        created_at: "2026-10-10T08:01:00Z",
        data: { changes: { number: { old: "TEST12", new: "TEST123" } } },
      },
    ],
  };
}

async function serveCard(page: Page, app = cardFixture()) {
  await page.route(`**/api/operator/applications/${app.id}`, (route) => {
    assertAuthenticated(route);
    return route.fulfill({ json: app });
  });
  await page.route("**/api/operator/documents/export-document/file", (route) =>
    route.fulfill({
      contentType: "image/png",
      body: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jh0kAAAAASUVORK5CYII=",
        "base64",
      ),
    }),
  );
  return app;
}

const expiring: ExpiringItem[] = [
  {
    application_id: "expired",
    full_name: "Тестовый Соискатель",
    doc_type: "passport_by",
    doc_label: "Паспорт Беларуси",
    field: "Срок действия",
    date: "2026-10-01",
    days_left: -9,
  },
  {
    application_id: "today",
    full_name: "Второй Соискатель",
    doc_type: "patent",
    doc_label: "Патент на работу",
    field: "Действует до",
    date: "2026-10-10",
    days_left: 0,
  },
  {
    application_id: "soon",
    full_name: "Третий Соискатель",
    doc_type: "residence_permit",
    doc_label: "Вид на жительство",
    field: "Срок действия",
    date: "2026-10-30",
    days_left: 20,
  },
];

test.beforeEach(async ({ page }) => {
  await seedOperatorSession(page);
  // No country lists are needed: all field/document labels below come from card/list responses.
  await page.route("**/api/public/countries", (route) => route.fulfill({ json: [] }));
});

test("uncatalogued fields keep server labels and card CSV preserves Cyrillic filename and bytes", async ({ page }) => {
  const app = await serveCard(page);
  await page.route(`**/api/operator/applications/${app.id}/export.csv`, async (route) => {
    assertAuthenticated(route);
    app.history.push({
      actor: "operator:test-operator",
      action: "card_exported",
      document_id: null,
      created_at: "2026-10-10T08:02:00Z",
      data: {},
    });
    await route.fulfill({
      contentType: "text/csv; charset=utf-8",
      headers: {
        "Content-Disposition": `attachment; filename="card.csv"; filename*=UTF-8''${encodeURIComponent("Тестовый Соискатель.csv")}`,
      },
      body: cardCsv,
    });
  });
  await page.goto(`/operator/applications/${app.id}`);
  await expect(page.getByLabel("Номер", { exact: true })).toHaveValue("TEST123");
  await expect(page.getByLabel("ФИО", { exact: true })).toHaveValue(app.full_name);
  await expect(page.getByText("Номер: TEST12 → TEST123")).toBeVisible();
  await expect(page.getByText("Поле документа", { exact: false })).toHaveCount(0);
  const pendingDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Выгрузить карточку (CSV)", exact: true }).click();
  const download = await pendingDownload;
  expect(download.suggestedFilename()).toBe("Тестовый Соискатель.csv");
  expect(await bytes(download)).toEqual(cardCsv);
  await expect(page.getByText("Карточка выгружена в CSV", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/export-card.png", fullPage: true });
});

test("expiry list distinguishes expired, today and future and exports the selected period", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route("**/api/operator/expiring?*", (route) => {
    assertAuthenticated(route);
    const days = Number(new URL(route.request().url()).searchParams.get("days"));
    return route.fulfill({ json: expiring.filter((item) => item.days_left <= days) });
  });
  await page.route("**/api/operator/expiring.csv?*", (route) => {
    assertAuthenticated(route);
    expect(new URL(route.request().url()).searchParams.get("days")).toBe("7");
    return route.fulfill({
      contentType: "text/csv; charset=utf-8",
      headers: { "Content-Disposition": 'attachment; filename="expiring.csv"' },
      body: listCsv,
    });
  });
  await page.goto("/operator/expiring");
  await expect(page.getByRole("link", { name: "Истекают", exact: true })).toHaveClass("active");
  await expect(page.getByText("Истёк 9 дн. назад", { exact: true })).toBeVisible();
  await expect(page.getByText("Истекает сегодня", { exact: true })).toBeVisible();
  await expect(page.getByText("Осталось 20 дн.", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: expiring[0].full_name })).toHaveAttribute(
    "href",
    "/operator/applications/expired",
  );
  await expect(page.locator(".expired-row")).toHaveCount(1);
  await expect(page.locator("time").first()).toHaveText("01.10.2026");
  await page.screenshot({ path: "test-results/expiring-desktop.png", fullPage: true });
  await page.getByLabel("Период проверки").selectOption("7");
  await expect(page.getByRole("heading", { name: "Найдено: 2", exact: true })).toBeVisible();
  await expect(page.getByText("Осталось 20 дн.", { exact: true })).toHaveCount(0);
  const pendingDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Скачать CSV", exact: true }).click();
  const download = await pendingDownload;
  expect(download.suggestedFilename()).toBe("expiring.csv");
  expect(await bytes(download)).toEqual(listCsv);
});

test("changing period hides stale results until the new request completes", async ({ page }) => {
  let completeRequest!: () => void;
  const ready = new Promise<void>((resolve) => {
    completeRequest = resolve;
  });
  await page.route("**/api/operator/expiring?*", async (route) => {
    if (new URL(route.request().url()).searchParams.get("days") === "7") {
      await ready;
      await route.fulfill({ json: [] });
    } else await route.fulfill({ json: expiring });
  });
  await page.goto("/operator/expiring");
  await expect(page.getByRole("heading", { name: "Найдено: 3" })).toBeVisible();
  await page.getByLabel("Период проверки").selectOption("7");
  await expect(page.getByRole("status")).toHaveText("Проверяем сроки документов…");
  await expect(page.getByRole("table")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Скачать CSV" })).toHaveCount(0);
  completeRequest();
  await expect(page.getByText("За выбранный период истекающих и просроченных документов нет.")).toBeVisible();
});

for (const status of [401, 403]) {
  test(`CSV ${status} shows the refusal without saving it and can be retried`, async ({ page }) => {
    const app = await serveCard(page);
    let rejected = true;
    const downloads: Download[] = [];
    page.on("download", (download) => downloads.push(download));
    await page.route(`**/api/operator/applications/${app.id}/export.csv`, (route) => {
      assertAuthenticated(route);
      return rejected
        ? route.fulfill({ status, json: { detail: "Нет доступа к выгрузке" } })
        : route.fulfill({
            contentType: "text/csv",
            headers: { "Content-Disposition": "attachment; filename=\"fallback.csv\"; filename*=UTF-8''%broken" },
            body: cardCsv,
          });
    });
    await page.goto(`/operator/applications/${app.id}`);
    const button = page.getByRole("button", { name: "Выгрузить карточку (CSV)", exact: true });
    await button.click();
    await expect(page.getByRole("alert")).toHaveText("Нет доступа к выгрузке");
    expect(downloads).toHaveLength(0);
    await expect(button).toBeEnabled();
    rejected = false;
    const pendingDownload = page.waitForEvent("download");
    await button.click();
    expect((await pendingDownload).suggestedFilename()).toBe("fallback.csv");
    await expect(page.getByRole("alert")).toHaveCount(0);
  });
}

test("HTML returned by a proxy is not downloaded as CSV", async ({ page }) => {
  const app = await serveCard(page);
  const downloads: Download[] = [];
  page.on("download", (download) => downloads.push(download));
  await page.route(`**/api/operator/applications/${app.id}/export.csv`, (route) =>
    route.fulfill({ contentType: "text/html", body: "<html>Gateway error</html>" }),
  );
  await page.goto(`/operator/applications/${app.id}`);
  await page.getByRole("button", { name: "Выгрузить карточку (CSV)", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Сервер не вернул CSV-файл. Попробуйте скачать ещё раз.");
  expect(downloads).toHaveLength(0);
});

test("session ending before a download does not send an unauthenticated request", async ({ page }) => {
  const app = await serveCard(page);
  let requests = 0;
  await page.route(`**/api/operator/applications/${app.id}/export.csv`, (route) => {
    requests++;
    return route.fulfill({ contentType: "text/csv", body: cardCsv });
  });
  await page.goto(`/operator/applications/${app.id}`);
  await expect(page.getByRole("heading", { name: app.full_name, exact: true })).toBeVisible();
  await page.evaluate(() => sessionStorage.removeItem("oidc.user:http://localhost:8080/realms/docs:operator-ui"));
  await page.getByRole("button", { name: "Выгрузить карточку (CSV)", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Сеанс завершён. Войдите в рабочее место оператора ещё раз.");
  expect(requests).toBe(0);
});

test("expiry list fetch failure can be retried and displays an empty result honestly", async ({ page }) => {
  let failed = true;
  await page.route("**/api/operator/expiring?*", (route) =>
    failed
      ? route.fulfill({ status: 503, json: { detail: "Сервис временно недоступен" } })
      : route.fulfill({ json: [] }),
  );
  await page.goto("/operator/expiring");
  await expect(page.getByRole("alert")).toContainText("Сервис временно недоступен");
  await expect(page.getByText("За выбранный период истекающих и просроченных документов нет.")).toHaveCount(0);
  failed = false;
  await page.getByRole("button", { name: "Повторить", exact: true }).click();
  await expect(page.getByText("За выбранный период истекающих и просроченных документов нет.")).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});
