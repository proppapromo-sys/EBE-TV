"use client";
import { useEffect, useState } from "react";
import { Auth, Studio, tokens, uploadToCloudflare } from "../../lib/api";

const STATUS_LABEL = { draft: "Draft", pending: "In review", published: "Live" };

export default function StudioPage() {
  const [me, setMe] = useState(null);
  const [shows, setShows] = useState([]);
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const meR = await Auth.me();
    if (meR.ok) setMe(meR.data.user);
    if (meR.ok && meR.data.user.is_creator) {
      const s = await Studio.shows();
      if (s.ok) setShows(s.data.shows);
    }
    setLoading(false);
  }

  useEffect(() => {
    if (!tokens.access) { location.href = "/login"; return; }
    refresh();
  }, []);

  async function becomeCreator() {
    setMsg("Enabling creator mode…");
    const r = await Studio.enable();
    if (r.ok) { setMsg(""); refresh(); } else setMsg("Could not enable creator mode.");
  }

  async function createShow() {
    if (!title.trim()) return;
    setMsg("Creating show…");
    const r = await Studio.saveShow({ title, description: desc });
    if (r.ok) { setTitle(""); setDesc(""); setMsg(""); refresh(); }
    else setMsg(r.data.detail || "Could not create show.");
  }

  async function uploadEpisode(show, file) {
    setMsg(`Uploading "${file.name}"…`);
    const season = await Studio.addSeason(show.id, 1);
    if (!season.ok) return setMsg("Could not create season.");
    const up = await Studio.uploadUrl();
    if (!up.ok) return setMsg(up.data.detail || "Video uploads need Cloudflare keys (CF_*).");
    const ok = await uploadToCloudflare(up.data.uploadURL, file);
    if (!ok) return setMsg("Upload to Cloudflare failed.");
    const epNum = (show.seasons?.[0]?.episodes?.length || 0) + 1;
    const ep = await Studio.addEpisode({
      season: season.data.id, number: epNum,
      title: `Episode ${epNum}`, video: up.data.video_id,
    });
    if (ep.ok) { setMsg("Episode uploaded."); refresh(); }
    else setMsg("Could not attach episode.");
  }

  async function checkStatus(show) {
    const eps = (show.seasons?.flatMap((se) => se.episodes) || []).filter((e) => !e.ready);
    if (eps.length === 0) return;
    setMsg("Checking transcode status…");
    await Promise.all(eps.map((e) => Studio.episodeStatus(e.id)));   // reconciles from Cloudflare
    setMsg("");
    refresh();
  }

  async function submit(show) {
    setMsg("Submitting for review…");
    const r = await Studio.submit(show.id);
    if (r.ok) { setMsg("Submitted — awaiting moderation."); refresh(); }
    else setMsg(r.data.detail || "Add an episode with a video first.");
  }

  if (loading) return <main className="wrap"><p className="muted">Loading…</p></main>;

  if (!me?.is_creator) {
    return (
      <main className="wrap">
        <h1>Become a creator</h1>
        <p className="muted" style={{ maxWidth: 560 }}>
          Upload your own shows and movies. You keep ownership and earn a share of subscription
          revenue based on watch time. Set up payouts anytime on the{" "}
          <a href="/creator" style={{ textDecoration: "underline" }}>creator dashboard</a>.
        </p>
        <button className="btn" style={{ marginTop: 16 }} onClick={becomeCreator}>
          Become a creator →
        </button>
        <p className="muted" style={{ marginTop: 12 }}>{msg}</p>
      </main>
    );
  }

  return (
    <main className="wrap">
      <h1>Creator studio</h1>
      <p className="muted">Upload shows, add episodes, submit for review.</p>

      {/* New show */}
      <div className="plan" style={{ marginTop: 20 }}>
        <h2>New show</h2>
        <input placeholder="Show title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="Short description" value={desc} onChange={(e) => setDesc(e.target.value)} />
        <button className="btn" style={{ marginTop: 12 }} onClick={createShow}>Create show</button>
      </div>

      {msg && <p className="muted" style={{ marginTop: 14 }}>{msg}</p>}

      {/* My shows */}
      <h2 style={{ marginTop: 28 }}>My shows</h2>
      {shows.length === 0 ? (
        <p className="muted">No shows yet. Create one above.</p>
      ) : (
        <div className="grid" style={{ gridTemplateColumns: "1fr", gap: 12, marginTop: 12 }}>
          {shows.map((s) => {
            const eps = s.seasons?.flatMap((se) => se.episodes) || [];
            return (
              <div className="plan" key={s.id}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <h2 style={{ margin: 0 }}>{s.title}</h2>
                  <span className={`pill pill-${s.status === "published" ? "paid"
                    : s.status === "pending" ? "pending" : "skipped"}`}>
                    {STATUS_LABEL[s.status] || s.status}
                  </span>
                </div>
                <p className="muted" style={{ marginTop: 6 }}>
                  {eps.length} episode{eps.length === 1 ? "" : "s"}
                  {eps.length > 0 && ` · ${eps.filter((e) => e.ready).length} ready`}
                </p>

                {s.status === "draft" && (
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
                    <label className="btn ghost" style={{ cursor: "pointer" }}>
                      + Upload episode
                      <input type="file" accept="video/*" style={{ display: "none" }}
                        onChange={(e) => e.target.files[0] && uploadEpisode(s, e.target.files[0])} />
                    </label>
                    {eps.some((e) => !e.ready) && (
                      <button className="btn ghost" onClick={() => checkStatus(s)}>
                        Check status
                      </button>
                    )}
                    {eps.length > 0 && (
                      <button className="btn" onClick={() => submit(s)}>Submit for review</button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}
