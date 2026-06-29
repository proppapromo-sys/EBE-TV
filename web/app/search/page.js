"use client";
import { useEffect, useState } from "react";
import { Catalog } from "../../lib/api";
import Poster from "../../components/Poster";

export default function Search() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);

  // Debounced live search.
  useEffect(() => {
    const term = q.trim();
    if (!term) { setResults([]); setSearched(false); return; }
    const t = setTimeout(async () => {
      const r = await Catalog.search(term);
      if (r.ok) { setResults(r.data.results); setSearched(true); }
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <main className="wrap">
      <h1>Search</h1>
      <input autoFocus placeholder="Search shows…" value={q}
             onChange={(e) => setQ(e.target.value)} />
      {searched && results.length === 0 && (
        <p className="muted" style={{ marginTop: 16 }}>No shows match “{q}”.</p>
      )}
      <div className="grid" style={{ marginTop: 20 }}>
        {results.map((s) => (
          <a className="card" key={s.id} href={`/show/${s.slug}`}>
            <div className="cardmedia"><Poster src={s.poster_url} title={s.title} /></div>
            <div className="t">{s.title}</div>
          </a>
        ))}
      </div>
    </main>
  );
}
