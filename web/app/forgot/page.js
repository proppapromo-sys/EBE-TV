"use client";
import { useState } from "react";
import { Auth } from "../../lib/api";

export default function Forgot() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  async function submit() {
    await Auth.requestReset(email.trim());
    setSent(true);                                   // always succeeds (no account probing)
  }

  return (
    <main>
      <div className="box">
        <h1>Reset password</h1>
        {sent ? (
          <p className="muted">If an account exists for <b>{email}</b>, we’ve emailed a reset
            link. Check your inbox.</p>
        ) : (
          <>
            <p className="muted" style={{ marginBottom: 12 }}>
              Enter your email and we’ll send a reset link.</p>
            <input placeholder="Email" type="email" value={email}
                   onChange={(e) => setEmail(e.target.value)} />
            <button className="btn" style={{ marginTop: 16, width: "100%" }} onClick={submit}>
              Send reset link
            </button>
          </>
        )}
        <p className="muted" style={{ marginTop: 12 }}><a href="/login">Back to sign in</a></p>
      </div>
    </main>
  );
}
