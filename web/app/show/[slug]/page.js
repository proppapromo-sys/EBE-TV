"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Catalog } from "../../../lib/api";

export default function ShowDetail() {
  const { slug } = useParams();
  const [show, setShow] = useState(null);

  useEffect(() => {
    if (slug) Catalog.show(slug).then((r) => r.ok && setShow(r.data));
  }, [slug]);

  if (!show) return <main className="wrap"><p className="muted">Loading…</p></main>;
  return (
    <main className="wrap">
      <div className="hero">
        <img src={show.hero_url || show.poster_url} alt={show.title} />
        <div className="meta"><h1>{show.title}</h1></div>
      </div>
      <p className="muted">{show.description}</p>
      {show.seasons.map((s) => (
        <div key={s.id}>
          <h2>{s.title || `Season ${s.number}`}</h2>
          <div className="grid">
            {s.episodes.map((ep) => (
              <a className="card" key={ep.id} href={`/watch/${ep.id}`}>
                <img src={ep.thumbnail_url} alt={ep.title} style={{ aspectRatio: "16/9" }} />
                <div className="t">{ep.number}. {ep.title}</div>
              </a>
            ))}
          </div>
        </div>
      ))}
    </main>
  );
}
