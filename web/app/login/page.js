"use client";
import { useState } from "react";
import { Auth, tokens } from "../../lib/api";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  async function go() {
    setMsg("…");
    const fn = mode === "login" ? Auth.login(email, password)
                                : Auth.register(email, password, "");
    const r = await fn;
    if (r.ok) { tokens.set(r.data); location.href = "/"; }
    else setMsg(r.data.detail || JSON.stringify(r.data));
  }

  return (
    <main>
      <div className="box">
        <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
        <input placeholder="Email" type="email" value={email}
               onChange={(e) => setEmail(e.target.value)} />
        <input placeholder="Password" type="password" value={password}
               onChange={(e) => setPassword(e.target.value)} />
        <button className="btn" style={{ marginTop: 16, width: "100%" }} onClick={go}>
          {mode === "login" ? "Sign in →" : "Create account →"}
        </button>
        <p className="muted" style={{ marginTop: 12 }}>{msg}</p>
        <p className="muted" style={{ cursor: "pointer" }}
           onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </p>
        {mode === "login" && <p className="muted"><a href="/forgot">Forgot password?</a></p>}
        <p className="muted">Demo: demo@demo.test / demopass123</p>
      </div>
    </main>
  );
}
