"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Auth, tokens } from "../lib/api";

const LINKS = [
  { href: "/", label: "Watch Now", icon: "▶" },
  { href: "/search", label: "Search", icon: "🔍" },
  { href: "/subscribe", label: "Subscribe", icon: "★" },
  { href: "/studio", label: "Creator Studio", icon: "🎬" },
  { href: "/creator", label: "Creator Payouts", icon: "＄" },
  { href: "/account", label: "Account", icon: "👤" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export default function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [me, setMe] = useState(null);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    if (!tokens.access) return;
    setAuthed(true);
    Auth.me().then((r) => r.ok && setMe(r.data.user));
  }, []);

  // Lock body scroll while the drawer is open.
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  function signOut() { Auth.logout(); location.href = "/"; }

  return (
    <>
      <nav className="nav">
        <button className="iconbtn" aria-label="Menu" onClick={() => setOpen(true)}>☰</button>
        <a className="brand" href="/">▶ STREAM</a>
        <span className="spacer" />
        <a href="/search" className="iconbtn" aria-label="Search">🔍</a>
        {authed
          ? <a href="/account" className="btn ghost">Account</a>
          : <a href="/login" className="btn ghost">Sign in</a>}
      </nav>

      {open && (
        <>
          <div className="drawer-overlay" onClick={() => setOpen(false)} />
          <aside className="drawer">
            <div className="drawer-acct">
              <span className="avatar">{(me?.email?.[0] || "👤").toUpperCase()}</span>
              <div style={{ overflow: "hidden" }}>
                <div style={{ fontWeight: 700, whiteSpace: "nowrap",
                  overflow: "hidden", textOverflow: "ellipsis" }}>
                  {me?.display_name || me?.email || "Guest"}
                </div>
                {me?.email && <div className="muted" style={{ fontSize: 13 }}>{me.email}</div>}
              </div>
            </div>

            {LINKS.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setOpen(false)}
                 className={`drawer-link${path === l.href ? " active" : ""}`}>
                <span style={{ width: 22, textAlign: "center" }}>{l.icon}</span>{l.label}
              </a>
            ))}

            {authed
              ? <button className="drawer-link" onClick={signOut}
                        style={{ background: "none", border: 0, cursor: "pointer", width: "100%",
                                 textAlign: "left", font: "inherit", color: "var(--fg)" }}>
                  <span style={{ width: 22, textAlign: "center" }}>⏻</span>Sign out
                </button>
              : <a href="/login" onClick={() => setOpen(false)} className="drawer-link">
                  <span style={{ width: 22, textAlign: "center" }}>→</span>Sign in
                </a>}

            <div className="drawer-foot">EBE-TV · v0.1</div>
          </aside>
        </>
      )}
    </>
  );
}
