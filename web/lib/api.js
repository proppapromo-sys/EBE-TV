// Tiny API client + JWT storage. Tokens live in localStorage; the access token rides on every
// authed request, and a 401 transparently refreshes once.
const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export const tokens = {
  get access() { return typeof window !== "undefined" ? localStorage.getItem("access") : null; },
  get refresh() { return typeof window !== "undefined" ? localStorage.getItem("refresh") : null; },
  set({ access, refresh }) {
    if (access) localStorage.setItem("access", access);
    if (refresh) localStorage.setItem("refresh", refresh);
  },
  clear() { localStorage.removeItem("access"); localStorage.removeItem("refresh"); },
};

async function raw(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && tokens.access) headers["Authorization"] = `Bearer ${tokens.access}`;
  const res = await fetch(`${BASE}${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

export async function api(path, opts = {}) {
  let r = await raw(path, opts);
  if (r.status === 401 && opts.auth && tokens.refresh) {
    const rf = await raw("/auth/refresh", { method: "POST", body: { refresh: tokens.refresh } });
    if (rf.ok) { tokens.set(rf.data); r = await raw(path, opts); }
  }
  return r;
}

export const Auth = {
  register: (email, password, display_name) =>
    raw("/auth/register", { method: "POST", body: { email, password, display_name } }),
  login: (email, password) =>
    raw("/auth/login", { method: "POST", body: { email, password } }),
  me: () => api("/me", { auth: true }),
  logout() { tokens.clear(); },
};

export const Catalog = {
  list: () => raw("/catalog"),
  show: (slug) => raw(`/shows/${slug}`),
};

export const Billing = {
  plans: () => raw("/plans"),
  checkout: (plan_code) =>
    api("/subscribe/stripe", { method: "POST", auth: true, body: { plan_code } }),
};

export const Playback = {
  play: (episodeId) => api(`/play/${episodeId}`, { auth: true }),
  progress: (episodeId, position_s) =>
    api(`/progress/${episodeId}`, { method: "POST", auth: true, body: { position_s } }),
};

export const Creator = {
  account: () => api("/creator/account", { auth: true }),
  onboard: () => api("/creator/onboard", { method: "POST", auth: true }),
  earnings: () => api("/creator/earnings", { auth: true }),
};
