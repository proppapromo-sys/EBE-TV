"use client";
import { useEffect, useState } from "react";
import { Catalog } from "../../lib/api";
import Poster from "../../components/Poster";

export default function Search() {
  const [q, setQ] = useState("");
  const [genre, setGenre] = useState("");
  const [genres, setGenres] = useState([]);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);

  // Load the genre facet once.
  useEffect(() => { Catalog.search("", "").then((r) => r.ok && setGenres(r.data.genres || [])); }, []);

  // Debounced live search whenever the query or genre changes.
  useEffect(() => {
    const term = q.trim();
    if (!term && !genre) { setResults([]); setSearched(false); return; }
    const t = setTimeout(async () => {
      const r = await Catalog.search(term, genre);
      if (r.ok) { setResults(r.data.results); setSearched(true); }
    }, 250);
    return () => clearTimeout(t);
  }, [q, genre]);

  return (
    <main className="wrap">
      <h1>Search</h1>
      <input autoFocus placeholder="Search shows…" value={q}
             onChange={(e) => setQ(e.target.value)} />

      {genres.length > 0 && (
        <div className="chips">
          <button className={`chip${genre === "" ? " on" : ""}`} onClick={() => setGenre("")}>
            All</button>
          {genres.map((g) => (
            <button key={g} className={`chip${genre === g ? " on" : ""}`}
                    onClick={() => setGenre(genre === g ? "" : g)}>{g}</button>
          ))}
        </div>
      )}

      {searched && results.length === 0 && (
        <p className="muted" style={{ marginTop: 16 }}>No shows match.</p>
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
