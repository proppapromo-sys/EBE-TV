"use client";
import { useEffect, useState } from "react";
import { Creator, tokens } from "../../lib/api";

const money = (cents, ccy = "usd") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: ccy.toUpperCase() })
    .format((cents || 0) / 100);

const fmtDate = (s) => (s ? new Date(s).toLocaleDateString() : "—");
const fmtSecs = (s) => `${Math.round((s || 0) / 60)} min`;

export default function CreatorDashboard() {
  const [account, setAccount] = useState(null);
  const [onboarded, setOnboarded] = useState(false);
  const [earnings, setEarnings] = useState([]);
  const [lifetime, setLifetime] = useState(0);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    const [acc, earn] = await Promise.all([Creator.account(), Creator.earnings()]);
    if (acc.ok) { setAccount(acc.data.account); setOnboarded(acc.data.onboarded); }
    if (earn.ok) { setEarnings(earn.data.earnings); setLifetime(earn.data.lifetime_net_cents); }
    setLoading(false);
  }

  useEffect(() => {
    if (!tokens.access) { location.href = "/login"; return; }
    load();
  }, []);

  async function onboard() {
    setMsg("Opening Stripe onboarding…");
    const r = await Creator.onboard();
    if (r.ok && r.data.onboarding_url) location.href = r.data.onboarding_url;
    else setMsg(r.data.detail || r.data.error || "Payouts unavailable (set Stripe keys).");
  }

  if (loading) return <main className="wrap"><p className="muted">Loading…</p></main>;

  const ccy = earnings[0]?.currency || "usd";
  const pending = earnings.filter((e) => e.status === "pending")
    .reduce((s, e) => s + e.net_cents, 0);

  return (
    <main className="wrap">
      <h1>Creator dashboard</h1>
      <p className="muted">Earnings from your shows, paid by watch-time share.</p>

      {/* Payout account status */}
      <div className="plan" style={{ marginTop: 20 }}>
        <h2>Payout account</h2>
        {onboarded ? (
          <p style={{ color: "#39d353" }}>✓ Connected — you're set up to receive payouts.</p>
        ) : (
          <>
            <p className="muted" style={{ marginBottom: 12 }}>
              {account?.stripe_account_id
                ? "Onboarding incomplete. Finish verification to get paid."
                : "Connect a payout account to start earning from your shows."}
            </p>
            <button className="btn" onClick={onboard}>
              {account?.stripe_account_id ? "Continue onboarding →" : "Set up payouts →"}
            </button>
          </>
        )}
        {msg && <p className="muted" style={{ marginTop: 10 }}>{msg}</p>}
      </div>

      {/* Earnings summary */}
      <div className="row" style={{ marginTop: 20 }}>
        <div className="plan">
          <p className="muted">Lifetime earnings (net)</p>
          <p style={{ fontSize: 30, fontWeight: 800 }}>{money(lifetime, ccy)}</p>
        </div>
        <div className="plan">
          <p className="muted">Pending payout</p>
          <p style={{ fontSize: 30, fontWeight: 800 }}>{money(pending, ccy)}</p>
        </div>
      </div>

      {/* Earnings ledger */}
      <h2 style={{ marginTop: 28 }}>Earnings by period</h2>
      {earnings.length === 0 ? (
        <p className="muted">No earnings yet. They appear once a payout period is computed.</p>
      ) : (
        <table className="ledger">
          <thead>
            <tr>
              <th>Period</th><th>Watch time</th><th>Share</th>
              <th>Gross</th><th>Fee</th><th>Net</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {earnings.map((e) => (
              <tr key={e.id}>
                <td>{fmtDate(e.period_start)} – {fmtDate(e.period_end)}</td>
                <td>{fmtSecs(e.watched_seconds)}</td>
                <td>{(e.share_bps / 100).toFixed(1)}%</td>
                <td>{money(e.gross_cents, e.currency)}</td>
                <td className="muted">−{money(e.fee_cents, e.currency)}</td>
                <td style={{ fontWeight: 700 }}>{money(e.net_cents, e.currency)}</td>
                <td><span className={`pill pill-${e.status}`}>{e.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
