"use client";
import { useEffect, useState } from "react";
import { Admin, Auth, tokens } from "../../lib/api";

export default function Moderate() {
  const [items, setItems] = useState([]);
  const [allowed, setAllowed] = useState(null);
  const [msg, setMsg] = useState("");

  async function load() {
    const me = await Auth.me();
    if (!me.ok || !me.data.user.is_staff) { setAllowed(false); return; }
    setAllowed(true);
    const r = await Admin.moderationQueue();
    if (r.ok) setItems(r.data.pending);
  }
  useEffect(() => {
    if (!tokens.access) { location.href = "/login"; return; }
    load();
  }, []);

  async function decide(id, action) {
    setMsg(action === "approve" ? "Publishing…" : "Rejecting…");
    const r = await Admin.moderate(id, action);
    if (r.ok) { setItems((xs) => xs.filter((x) => x.id !== id)); setMsg(""); }
    else setMsg("Action failed.");
  }

  if (allowed === false) return <main className="wrap"><p className="muted">Staff only.</p></main>;
  if (allowed === null) return <main className="wrap"><p className="muted">Loading…</p></main>;

  return (
    <main className="wrap" style={{ maxWidth: 760 }}>
      <h1>Moderation queue</h1>
      <p className="muted">Creator submissions awaiting review.</p>
      {msg && <p className="muted">{msg}</p>}
      {items.length === 0 ? (
        <p className="muted" style={{ marginTop: 16 }}>Nothing pending. 🎉</p>
      ) : (
        items.map((s) => (
          <div className="plan" key={s.id} style={{ marginTop: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <h2 style={{ margin: 0 }}>{s.title}</h2>
                <p className="muted" style={{ margin: "4px 0 0" }}>
                  {s.owner_email || "—"} · {s.ready_episodes}/{s.episodes} episodes ready
                </p>
              </div>
              <button className="btn" onClick={() => decide(s.id, "approve")}>Approve</button>
              <button className="btn ghost" onClick={() => decide(s.id, "reject")}>Reject</button>
            </div>
          </div>
        ))
      )}
    </main>
  );
}
