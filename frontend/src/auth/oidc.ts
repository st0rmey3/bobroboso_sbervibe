import { UserManager, WebStorageStateStore } from "oidc-client-ts";

// Keycloak realm "docs", public client "operator-ui", Authorization Code + PKCE.
// PKCE needs a secure context: open the stand via http://localhost or https (not a bare IP over http).
const authority = import.meta.env.VITE_OIDC_AUTHORITY ?? `${location.protocol}//${location.hostname}:8080/realms/docs`;

export const userManager = new UserManager({
  authority,
  client_id: "operator-ui",
  redirect_uri: `${location.origin}/operator/callback`,
  post_logout_redirect_uri: `${location.origin}/operator`,
  response_type: "code",
  scope: "openid profile",
  userStore: new WebStorageStateStore({ store: sessionStorage }),
  automaticSilentRenew: true,
});

export async function accessToken(): Promise<string | null> {
  const user = await userManager.getUser();
  return user && !user.expired ? user.access_token : null;
}
