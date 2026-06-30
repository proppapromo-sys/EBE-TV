"use client";
import { useEffect, useState } from "react";
import { getPrefs, setPref } from "../../lib/prefs";

function Toggle({ on, onClick }) {
  return (
    <button className={`toggle${on ? " on" : ""}`} onClick={onClick}
            aria-pressed={on} aria-label="toggle"><span className="knob" /></button>
  );
}

export default function Settings() {
  const [prefs, setPrefs] = useState(null);
  useEffect(() => { setPrefs(getPrefs()); }, []);
  if (!prefs) return <main className="wrap"><p className="muted">Loading…</p></main>;

  const update = (k, v) => setPrefs(setPref(k, v));

  return (
    <main className="wrap" style={{ maxWidth: 640 }}>
      <h1>Settings</h1>

      <div className="setgroup">
        <div className="setrow">
          <span className="lbl"><span className="ico">⚙</span>Preferred quality</span>
          <select className="pref" value={prefs.quality}
                  onChange={(e) => update("quality", e.target.value)}>
            <option value="auto">Auto</option>
            <option value="1080">1080p</option>
            <option value="720">720p</option>
            <option value="480">480p (Data saver)</option>
          </select>
        </div>
        <div className="setrow">
          <span className="lbl"><span className="ico">▶</span>Auto-play</span>
          <Toggle on={prefs.autoplay} onClick={() => update("autoplay", !prefs.autoplay)} />
        </div>
        <div className="setrow">
          <span className="lbl"><span className="ico">📶</span>Data saver</span>
          <Toggle on={prefs.dataSaver} onClick={() => update("dataSaver", !prefs.dataSaver)} />
        </div>
      </div>

      <div className="setgroup">
        <a className="setrow" href="/subscribe">
          <span className="lbl"><span className="ico">★</span>Manage subscription</span>
          <span className="muted">›</span>
        </a>
        <a className="setrow" href="/account">
          <span className="lbl"><span className="ico">👤</span>Account</span>
          <span className="muted">›</span>
        </a>
      </div>

      <div className="setgroup">
        <a className="setrow" href="mailto:support@ebe.tv"><span className="lbl"><span className="ico">✉</span>Feedback</span><span className="muted">🔗</span></a>
        <a className="setrow" href="/terms"><span className="lbl"><span className="ico">📄</span>Terms of Use</span><span className="muted">›</span></a>
        <a className="setrow" href="/privacy"><span className="lbl"><span className="ico">🛡</span>Privacy Policy</span><span className="muted">›</span></a>
      </div>

      <p className="muted" style={{ marginTop: 16 }}>EBE·TV · v0.1</p>
    </main>
  );
}
