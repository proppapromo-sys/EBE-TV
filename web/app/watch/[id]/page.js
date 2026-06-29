"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Playback, tokens } from "../../../lib/api";
import { getPrefs, maxHeightFor } from "../../../lib/prefs";

export default function Watch() {
  const { id } = useParams();
  const videoRef = useRef(null);
  const playerRef = useRef(null);
  const [status, setStatus] = useState("loading");   // loading | buffering | playing | error
  const [error, setError] = useState("");
  const [captions, setCaptions] = useState([]);
  const [ccOn, setCcOn] = useState(false);

  async function start() {
    setStatus("loading"); setError("");
    const r = await Playback.play(id);
    if (r.status === 403) { location.href = "/subscribe"; return; }
    if (!r.ok) { setStatus("error"); setError(r.data.detail || r.data.error || "Cannot play this episode."); return; }

    setCaptions(r.data.captions || []);
    const prefs = getPrefs();
    const video = videoRef.current;
    video.autoplay = prefs.autoplay;

    try {
      const shaka = (await import("shaka-player/dist/shaka-player.compiled.js")).default;
      shaka.polyfill.installAll();
      if (video.canPlayType("application/vnd.apple.mpegurl") && r.data.manifest.hls) {
        video.src = r.data.manifest.hls;                       // Safari / FairPlay
      } else if (shaka.Player.isBrowserSupported()) {
        const player = new shaka.Player(video);
        playerRef.current = player;
        // Resilience: retry a stalled/failed segment a few times before giving up.
        player.configure({
          streaming: { retryParameters: { maxAttempts: 5, baseDelay: 500, backoffFactor: 1.5 },
                       bufferingGoal: 20, rebufferingGoal: 4 },
        });
        const cap = prefs.dataSaver ? 480 : maxHeightFor(prefs.quality);
        if (cap) player.configure({ restrictions: { maxHeight: cap } });
        player.addEventListener("buffering", (e) =>
          setStatus(e.buffering ? "buffering" : "playing"));
        player.addEventListener("error", (e) => onFatal(e.detail));
        await player.load(r.data.manifest.dash);               // Widevine/PlayReady
      } else {
        setStatus("error"); setError("This browser can't play DRM-protected video."); return;
      }
    } catch (e) {
      onFatal(e); return;
    }

    if (r.data.resume_position_s) video.currentTime = r.data.resume_position_s;
    setStatus("playing");

    const t = setInterval(() => {
      if (!video.paused) Playback.progress(id, Math.floor(video.currentTime));
    }, 15000);
    video.addEventListener("ended", () => clearInterval(t));
  }

  let fatalCount = 0;
  function onFatal(detail) {
    // Transient network errors → one silent retry; otherwise surface a Retry button.
    if (fatalCount++ < 1) { start(); return; }
    setStatus("error");
    setError("Playback was interrupted. Check your connection and try again.");
  }

  useEffect(() => {
    if (!id) return;
    if (!tokens.access) { location.href = "/login"; return; }
    start();
    return () => { if (playerRef.current) playerRef.current.destroy(); };
  }, [id]);

  function toggleCaptions() {
    const on = !ccOn; setCcOn(on);
    const player = playerRef.current, video = videoRef.current;
    if (player) {
      player.setTextTrackVisibility(on);
      if (on && captions[0]) player.selectTextLanguage(captions[0].language);
    } else if (video) {                                        // native HLS (Safari)
      for (const tr of video.textTracks) tr.mode = on ? "showing" : "disabled";
    }
  }

  return (
    <main className="wrap">
      <div className="playerwrap">
        <video ref={videoRef} controls playsInline />
        {(status === "loading" || status === "buffering") && (
          <div className="playoverlay"><div className="spinner" /></div>
        )}
        {status === "error" && (
          <div className="playoverlay col">
            <p>{error}</p>
            <button className="btn" onClick={() => { fatalCount = 0; start(); }}>Retry</button>
          </div>
        )}
      </div>
      {captions.length > 0 && status !== "error" && (
        <button className="btn ghost" style={{ marginTop: 12 }} onClick={toggleCaptions}>
          {ccOn ? "CC on" : "CC off"} · {captions.map((c) => c.label).join(", ")}
        </button>
      )}
    </main>
  );
}
