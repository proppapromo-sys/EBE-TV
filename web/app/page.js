"use client";
import { useEffect, useState } from "react";
import { Catalog } from "../lib/api";

export default function Browse() {
  const [shows, setShows] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    Catalog.list().then((r) => r.ok ? setShows(r.data.shows) : setErr("Could not load catalog"));
  }, []);

  const hero = shows[0];
  return (
    <main className="wrap">
      {err && <p className="muted">{err} — is the backend running on :8000?</p>}
      {hero && (
        <a className="hero" href={`/show/${hero.slug}`}>
          <img src={hero.hero_url || hero.poster_url} alt={hero.title} />
          <div className="meta">
            <h1>{hero.title}</h1>
            <p className="muted">{(hero.genre || []).join(" · ")}</p>
          </div>
        </a>
      )}
      <h2>All shows</h2>
      <div className="grid">
        {shows.map((s) => (
          <a className="card" key={s.id} href={`/show/${s.slug}`}>
            <img src={s.poster_url} alt={s.title} />
            <div className="t">{s.title}</div>
          </a>
        ))}
      </div>
    </main>
  );
}
