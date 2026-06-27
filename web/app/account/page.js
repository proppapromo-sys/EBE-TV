"use client";
import { useEffect, useState } from "react";
import { Auth, Billing, tokens } from "../../lib/api";

const fmtDate = (s) => (s ? new Date(s).toLocaleDateString(undefined,
  { year: "numeric", month: "long", day: "numeric" }) : "—");
const SOURCE_LABEL = { stripe: "Web (card)", apple: "Apple App Store", google: "Google Play" };

export default function Account() {
  const [user, setUser] = useState(null);
  const [sub, setSub] = useState(null);
  const [msg, setMsg] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    const r = await Auth.me();
    if (r.ok) { setUser(r.data.user); setSub(r.data.subscription); }
    setLoading(false);
  }
  useEffect(() => {
    if (!tokens.access) { location.href = "/login"; return; }
    load();
  }, []);

  async function cancel() {
    setMsg("Canceling…"); setConfirming(false);
    const r = await Billing.cancel();
    if (r.ok) { setMsg(""); load(); }
    else if (r.data.error === "manage_in_store") {
      setMsg(r.data.detail);
      if (r.data.manage_url) window.open(r.data.manage_url, "_blank");
    } else setMsg(r.data.detail || r.data.error || "Could not cancel. Try again.");
  }

  function signOut() { Auth.logout(); location.href = "/"; }

  if (loading) return <main className="wrap"><p className="muted">Loading…</p></main>;

  const active = sub?.status === "active";
  const canceling = sub?.cancel_at_period_end;

  return (
    <main className="wrap" style={{ maxWidth: 640 }}>
      <h1>Account</h1>

      {/* Profile */}
      <div className="plan" style={{ marginTop: 16 }}>
        <p className="muted">Signed in as</p>
        <p style={{ fontSize: 18, fontWeight: 700 }}>{user?.email}</p>
        {user?.display_name && <p className="muted">{user.display_name}</p>}
      </div>

      {/* Subscription — management is front and center, not hidden. */}
      <div className="plan" style={{ marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Subscription</h2>
        {!active && !canceling ? (
          <>
            <p className="muted">You don’t have an active subscription.</p>
            <a className="btn" href="/subscribe" style={{ display: "inline-block", marginTop: 8 }}>
              See plans →
            </a>
          </>
        ) : (
          <>
            <div className="subrow"><span className="muted">Plan</span>
              <span style={{ textTransform: "capitalize" }}>{sub.plan || "—"}</span></div>
            <div className="subrow"><span className="muted">Status</span>
              <span className={`pill pill-${canceling ? "pending" : "paid"}`}>
                {canceling ? "Cancels at period end" : "Active"}</span></div>
            <div className="subrow"><span className="muted">Billed via</span>
              <span>{SOURCE_LABEL[sub.source] || sub.source}</span></div>
            <div className="subrow"><span className="muted">
              {canceling ? "Access until" : "Renews on"}</span>
              <span>{fmtDate(sub.current_period_end)}</span></div>

            {canceling ? (
              <p className="muted" style={{ marginTop: 12 }}>
                Your subscription is set to end — you’ll keep access until{" "}
                {fmtDate(sub.current_period_end)}.
              </p>
            ) : confirming ? (
              <div style={{ marginTop: 14 }}>
                <p style={{ marginBottom: 10 }}>
                  Cancel your subscription? You’ll keep access until{" "}
                  {fmtDate(sub.current_period_end)}.
                </p>
                <button className="btn" style={{ background: "#3a1414", color: "#f0635b" }}
                        onClick={cancel}>Yes, cancel</button>{" "}
                <button className="btn ghost" onClick={() => setConfirming(false)}>Keep plan</button>
              </div>
            ) : (
              <button className="btn ghost" style={{ marginTop: 14 }}
                      onClick={() => setConfirming(true)}>Cancel subscription</button>
            )}
          </>
        )}
        {msg && <p className="muted" style={{ marginTop: 12 }}>{msg}</p>}
      </div>

      <button className="btn ghost" style={{ marginTop: 16 }} onClick={signOut}>Sign out</button>
    </main>
  );
}
