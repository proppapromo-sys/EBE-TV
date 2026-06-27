"use client";
import { useEffect, useState } from "react";
import { Catalog } from "../lib/api";

function Row({ title, items }) {
  if (!items?.length) return null;
  return (
    <section className="rowblock">
      <a className="rowhead" href={`/show/${items[0].slug}`}>
        <h2>{title}</h2><span className="chev">›</span>
      </a>
      <div className="scroller">
        {items.map((s) => (
          <a className="poster" key={s.id + title} href={`/show/${s.slug}`}>
            <img src={s.poster_url} alt={s.title} loading="lazy" />
            <div className="postert">{s.title}</div>
          </a>
        ))}
      </div>
    </section>
  );
}

export default function Browse() {
  const [hero, setHero] = useState([]);
  const [rows, setRows] = useState([]);
  const [idx, setIdx] = useState(0);
  const [err, setErr] = useState("");

  useEffect(() => {
    Catalog.home().then((r) => {
      if (!r.ok) { setErr("Could not load catalog"); return; }
      setHero(r.data.hero || []);
      setRows(r.data.rows || []);
    });
  }, []);

  // Auto-advance the hero carousel.
  useEffect(() => {
    if (hero.length < 2) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % hero.length), 5000);
    return () => clearInterval(t);
  }, [hero]);

  const feature = hero[idx];
  return (
    <main>
      {err && <p className="muted wrap">{err} — is the backend running on :8000?</p>}

      {feature && (
        <a className="herobig" href={`/show/${feature.slug}`}>
          <img src={feature.hero_url || feature.poster_url} alt={feature.title} />
          <div className="herograd" />
          <div className="herometa">
            <h1>{feature.title}</h1>
            <p className="muted">{(feature.genre || []).join(" · ")}</p>
          </div>
          {hero.length > 1 && (
            <div className="dots">
              {hero.map((_, i) => (
                <span key={i} className={i === idx ? "dot on" : "dot"}
                  onClick={(e) => { e.preventDefault(); setIdx(i); }} />
              ))}
            </div>
          )}
        </a>
      )}

      <div className="rows">
        {rows.map((row) => <Row key={row.slug} title={row.title} items={row.items} />)}
        {!err && rows.length === 0 && (
          <p className="muted wrap">No collections yet. Run <code>manage.py seed_demo</code>.</p>
        )}
      </div>
    </main>
  );
}
