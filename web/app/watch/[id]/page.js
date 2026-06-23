"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Playback, tokens } from "../../../lib/api";

export default function Watch() {
  const { id } = useParams();
  const videoRef = useRef(null);
  const [msg, setMsg] = useState("Loading…");

  useEffect(() => {
    if (!id) return;
    if (!tokens.access) { location.href = "/login"; return; }

    let player;
    (async () => {
      const r = await Playback.play(id);
      if (r.status === 403) { setMsg("This requires a subscription."); location.href = "/subscribe"; return; }
      if (!r.ok) { setMsg(r.data.detail || r.data.error || "Cannot play this episode."); return; }

      setMsg("");
      // Shaka Player handles DASH + Widevine/PlayReady; Safari falls back to native HLS/FairPlay.
      const shaka = (await import("shaka-player/dist/shaka-player.compiled.js")).default;
      shaka.polyfill.installAll();
      const video = videoRef.current;
      if (video.canPlayType("application/vnd.apple.mpegurl") && r.data.manifest.hls) {
        video.src = r.data.manifest.hls;                 // Safari / FairPlay
      } else if (shaka.Player.isBrowserSupported()) {
        player = new shaka.Player(video);
        await player.load(r.data.manifest.dash);         // Chrome/Edge/Firefox / Widevine
      } else {
        setMsg("This browser can't play DRM-protected video.");
        return;
      }
      if (r.data.resume_position_s) video.currentTime = r.data.resume_position_s;

      // Save progress every 15s
      const t = setInterval(() => {
        if (!video.paused) Playback.progress(id, Math.floor(video.currentTime));
      }, 15000);
      video.addEventListener("ended", () => clearInterval(t));
    })();

    return () => { if (player) player.destroy(); };
  }, [id]);

  return (
    <main className="wrap">
      <video ref={videoRef} controls autoPlay />
      {msg && <p className="muted">{msg}</p>}
    </main>
  );
}
