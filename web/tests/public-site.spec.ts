import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function fillLead(page: Page) {
  await page.goto("/contacts");
  await page.getByLabel("Имя", { exact: true }).fill("Анна");
  await page.getByLabel("Telegram или e-mail", { exact: true }).fill("@anna_photo");
  await page.getByRole("checkbox").check();
}

for (const edit of ["none", "contact", "whitespace"] as const) {
  test(`retry after network failure: ${edit}`, async ({ page }) => {
    const requests: { key: string; contact: string }[] = [];
    await page.route("**/api/v1/leads", async (route) => {
      const request = route.request();
      requests.push({
        key: request.headers()["idempotency-key"],
        contact: request.postDataJSON().contact,
      });
      if (requests.length === 1) return route.abort("failed");
      await route.fulfill({ json: { public_number: "2026-00001", expected_response: "в течение суток" } });
    });
    await fillLead(page);
    await page.getByRole("button", { name: "Отправить заявку", exact: true }).click();
    await expect(page.getByRole("form", { name: "Заявка на съёмку" }).getByRole("alert")).toContainText("Нет связи с сервером");
    if (edit !== "none") {
      await page.getByLabel("Telegram или e-mail", { exact: true }).fill(
        edit === "contact" ? "@another_contact" : "  @anna_photo  ",
      );
    }
    await page.getByRole("button", { name: "Отправить заявку", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Заявка отправлена" })).toBeFocused();
    expect(requests).toHaveLength(2);
    if (edit === "contact") {
      expect(requests[1].key).not.toBe(requests[0].key);
      expect(requests[1].contact).toBe("@another_contact");
    } else {
      expect(requests[1].key).toBe(requests[0].key);
      expect(requests[1].contact).toBe("@anna_photo");
    }
  });
}

test("invalid form focuses the first field without sending", async ({ page }) => {
  let requests = 0;
  await page.route("**/api/v1/leads", (route) => { requests++; return route.abort(); });
  await page.goto("/contacts");
  await page.getByRole("button", { name: "Отправить заявку", exact: true }).click();
  await expect(page.getByLabel("Имя", { exact: true })).toBeFocused();
  await expect(page.getByLabel("Имя", { exact: true })).toHaveAttribute("aria-invalid", "true");
  expect(requests).toBe(0);
});

test("server validation errors focus the affected field", async ({ page }) => {
  await page.route("**/api/v1/leads", (route) => route.fulfill({ status: 422, json: {
    error: { code: "validation_error", message: "Проверьте поля", fields: { contact: "Проверьте контакт" } },
  } }));
  await fillLead(page);
  await page.getByRole("button", { name: "Отправить заявку", exact: true }).click();
  await expect(page.getByLabel("Telegram или e-mail", { exact: true })).toBeFocused();
  await expect(page.getByText("Проверьте контакт", { exact: true })).toBeVisible();
});

test("mobile menu includes the toggle in its keyboard focus cycle", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const toggle = page.getByRole("button", { name: "Открыть меню" });
  const nav = page.getByRole("navigation", { name: "Основная навигация" });
  await toggle.click();
  await expect(nav.getByRole("link").first()).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(page.getByRole("button", { name: "Закрыть меню" })).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(nav.getByRole("link").last()).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Закрыть меню" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(toggle).toBeFocused();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
});

test("lightbox navigation and focus restoration", async ({ page }) => {
  await page.goto("/portfolio");
  const frame = page.getByRole("button", { name: "Открыть кадр 01A: Тверская, утро" });
  await frame.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await page.keyboard.press("ArrowRight");
  await expect(dialog.getByRole("heading")).toHaveText("Метро");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(frame).toBeFocused();
});

test("unknown pages and catalog entries return 404", async ({ page }) => {
  for (const path of ["/missing", "/services/missing", "/portfolio/missing"]) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(404);
  }
});
