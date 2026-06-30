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
  requestReset: (email) => raw("/auth/password/reset", { method: "POST", body: { email } }),
  confirmReset: (uid, token, password) =>
    raw("/auth/password/reset/confirm", { method: "POST", body: { uid, token, password } }),
  logout() { tokens.clear(); },
};

export const Catalog = {
  list: () => raw("/catalog"),
  home: () => api("/home", { auth: true }),   // auth'd → personalized rows (Continue Watching)
  search: (q, genre = "") =>
    raw(`/search?q=${encodeURIComponent(q)}&genre=${encodeURIComponent(genre)}`),
  show: (slug) => raw(`/shows/${slug}`),
};

export const Billing = {
  plans: () => raw("/plans"),
  checkout: (plan_code) =>
    api("/subscribe/stripe", { method: "POST", auth: true, body: { plan_code } }),
  cancel: () => api("/subscribe/cancel", { method: "POST", auth: true }),
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

export const Admin = {
  moderationQueue: () => api("/cms/moderation", { auth: true }),
  moderate: (id, action) =>
    api("/cms/moderation", { method: "POST", auth: true, body: { id, action } }),
};

export const Studio = {
  enable: () => api("/studio/enable", { method: "POST", auth: true }),
  shows: () => api("/studio/shows", { auth: true }),
  saveShow: (show) => api("/studio/shows", { method: "POST", auth: true, body: show }),
  addSeason: (showId, number = 1) =>
    api("/studio/seasons", { method: "POST", auth: true, body: { show: showId, number } }),
  uploadUrl: () => api("/studio/videos/upload-url", { method: "POST", auth: true, body: {} }),
  addEpisode: (ep) => api("/studio/episodes", { method: "POST", auth: true, body: ep }),
  episodeStatus: (episodeId) => api(`/studio/episodes/${episodeId}/status`, { auth: true }),
  submit: (showId) => api("/studio/submit", { method: "POST", auth: true, body: { show: showId } }),
};

// PUT a file straight to a Cloudflare direct-upload URL (off-API, no auth header).
export async function uploadToCloudflare(uploadURL, file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(uploadURL, { method: "POST", body: form });
  return res.ok;
}
