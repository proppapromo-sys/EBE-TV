"use client";
import { useState } from "react";

// Never a broken image: renders the artwork, or a branded placeholder (title initials) when the
// URL is missing OR fails to load.
export default function Poster({ src, title }) {
  const [broken, setBroken] = useState(false);
  if (!src || broken) {
    return <div className="posterph">{(title || "?").slice(0, 2).toUpperCase()}</div>;
  }
  return <img src={src} alt={title} loading="lazy" onError={() => setBroken(true)} />;
}
