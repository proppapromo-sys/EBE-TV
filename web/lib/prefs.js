// Device playback preferences, persisted in localStorage (these are per-device, like the
// reference app's Settings). Read by the player; edited on /settings.
const DEFAULTS = { quality: "auto", autoplay: true, dataSaver: false };

export function getPrefs() {
  if (typeof window === "undefined") return { ...DEFAULTS };
  try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem("prefs") || "{}") }; }
  catch { return { ...DEFAULTS }; }
}

export function setPref(key, value) {
  const next = { ...getPrefs(), [key]: value };
  localStorage.setItem("prefs", JSON.stringify(next));
  return next;
}

// Map a quality preference to a max video height for the player (null = unrestricted).
export function maxHeightFor(quality) {
  return { "1080": 1080, "720": 720, "480": 480 }[quality] || null;
}
