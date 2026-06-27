"use client";
import { useEffect, useState } from "react";
import { Billing, tokens } from "../../lib/api";

export default function Subscribe() {
  const [plans, setPlans] = useState([]);
  const [msg, setMsg] = useState("");

  useEffect(() => { Billing.plans().then((r) => r.ok && setPlans(r.data.plans)); }, []);

  async function subscribe(code) {
    if (!tokens.access) { location.href = "/login"; return; }
    setMsg("Creating checkout…");
    const r = await Billing.checkout(code);
    if (r.ok && r.data.checkout_url) location.href = r.data.checkout_url;
    else setMsg(r.data.detail || r.data.error || "Checkout unavailable (set Stripe keys).");
  }

  return (
    <main className="wrap">
      <h1>Everything EBE. One pass.</h1>
      <p className="muted">Every original series and live event on EBE·TV. Cancel anytime.</p>
      <div className="row" style={{ marginTop: 20 }}>
        {plans.map((p) => (
          <div className="plan" key={p.id}>
            <h2 style={{ textTransform: "capitalize" }}>{p.code}</h2>
            <p style={{ fontSize: 30, fontWeight: 800 }}>
              ${p.price}<span className="muted" style={{ fontSize: 14 }}>/{p.interval}</span>
            </p>
            <button className="btn" onClick={() => subscribe(p.code)}>Subscribe</button>
          </div>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 16 }}>{msg}</p>
    </main>
  );
}
