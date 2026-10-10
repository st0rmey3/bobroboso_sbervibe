import type { Page } from "@playwright/test";

export async function seedOperatorSession(page: Page) {
  // Only test browsers receive this token; production still verifies real JWTs server-side.
  await page.addInitScript(() =>
    sessionStorage.setItem(
      "oidc.user:http://localhost:8080/realms/docs:operator-ui",
      JSON.stringify({
        access_token: "synthetic-operator-token",
        token_type: "Bearer",
        scope: "openid profile",
        profile: { sub: "test-operator" },
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      }),
    ),
  );
}
