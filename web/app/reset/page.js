"use client";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Auth } from "../../lib/api";

function ResetForm() {
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [done, setDone] = useState(false);

  async function submit() {
    if (password.length < 8) { setMsg("Password must be at least 8 characters."); return; }
    setMsg("Saving…");
    const r = await Auth.confirmReset(uid, token, password);
    if (r.ok) { setDone(true); setMsg(""); }
    else setMsg(r.data.error === "invalid_or_expired"
      ? "This link is invalid or expired. Request a new one." : "Could not reset. Try again.");
  }

  if (!uid || !token) return <p className="muted">Invalid reset link.</p>;
  return done ? (
    <>
      <p style={{ color: "#39d353" }}>Password updated.</p>
      <a className="btn" style={{ marginTop: 12, display: "inline-block" }} href="/login">
        Sign in</a>
    </>
  ) : (
    <>
      <p className="muted" style={{ marginBottom: 12 }}>Choose a new password.</p>
      <input placeholder="New password" type="password" value={password}
             onChange={(e) => setPassword(e.target.value)} />
      <button className="btn" style={{ marginTop: 16, width: "100%" }} onClick={submit}>
        Set new password</button>
      <p className="muted" style={{ marginTop: 12 }}>{msg}</p>
    </>
  );
}

export default function Reset() {
  return (
    <main>
      <div className="box">
        <h1>New password</h1>
        <Suspense fallback={<p className="muted">Loading…</p>}><ResetForm /></Suspense>
      </div>
    </main>
  );
}
