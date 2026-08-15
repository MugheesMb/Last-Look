"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const OCCASIONS = [
  { value: "interview", label: "Job interview" },
  { value: "first_date", label: "First date" },
  { value: "wedding_guest", label: "Wedding guest" },
];

const GENDERS = [
  { value: "women", label: "Women" },
  { value: "men", label: "Men" },
];

const STEPS = [
  { n: "01", label: "Pick your occasion" },
  { n: "02", label: "Upload your picture" },
  { n: "03", label: "Get your skin plan" },
  { n: "04", label: "See color-verified outfits" },
  { n: "05", label: "Shop the look" },
];

export default function Page() {
  const [occasion, setOccasion] = useState("interview");
  const [gender, setGender] = useState("women");
  const [daysUntil, setDaysUntil] = useState(3);
  const [location, setLocation] = useState("");
  const [selfie, setSelfie] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [log, setLog] = useState([]);

  function onSelfieChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelfie(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!selfie) {
      setError("Upload a picture first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setLog([]);

    const form = new FormData();
    form.append("occasion", occasion);
    form.append("gender", gender);
    form.append("days_until", String(daysUntil));
    form.append("location", location);
    form.append("selfie", selfie);

    try {
      const res = await fetch(`${API_BASE}/api/countdown`, { method: "POST", body: form });
      if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          const event = JSON.parse(line);
          if (event.type === "progress") setLog((prev) => [...prev, event.label]);
          else if (event.type === "error") throw new Error(event.message);
          else if (event.type === "done") setResult(event.data);
        }
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-cream text-ink">
      {/* Nav */}
      <div className="border-b border-line">
        <div className="max-w-6xl mx-auto px-8 py-5 flex items-center justify-between">
          <span className="font-display italic text-xl">Last Look</span>
          <span className="font-mono text-xs tracking-widest text-muted uppercase">Multi-Agent AI Concierge</span>
        </div>
      </div>

      {/* Hero */}
      <div className="max-w-6xl mx-auto px-8 py-16 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-14 items-center">
        <div>
          <p className="font-mono text-xs tracking-[0.25em] text-sage uppercase mb-4">
            Agentic AI · Skin + Style + Weather
          </p>
          <h1 className="font-display text-4xl sm:text-5xl leading-[1.1] mb-5">
            Prepared for the moment — <span className="italic">down to the weather.</span>
          </h1>
          <p className="text-muted text-base max-w-md leading-relaxed mb-6">
            A self-verifying agent pipeline runs real AI skin diagnostics, color-theory outfit try-ons, and live
            weather for your event day — checking its own work before you ever see it.
          </p>
          <div className="flex flex-wrap gap-2">
            {["AI Skin Diagnostics", "Color-Verified Try-On", "Live Weather Data"].map((tag) => (
              <span
                key={tag}
                className="font-mono text-[11px] tracking-wide uppercase border border-line rounded-full px-3 py-1.5 text-muted"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="bg-sagelight rounded-2xl aspect-[4/3] flex flex-col items-center justify-center border border-line">
            <span key={daysUntil} className="tick font-display italic text-7xl text-ink">
              {daysUntil}
            </span>
            <span className="font-script text-2xl text-sage mt-1">days to go</span>
          </div>
          <div className="absolute -bottom-5 -left-5 bg-panel border border-line rounded-xl px-4 py-3 shadow-sm">
            <p className="font-mono text-[10px] tracking-widest text-muted uppercase">Verified by</p>
            <p className="text-sm font-medium">Skin AI · Color Theory · Weather</p>
          </div>
        </div>
      </div>

      {/* How it works — numbered, a real sequence */}
      <div className="border-y border-line bg-panel">
        <div className="max-w-6xl mx-auto px-8 py-6 grid grid-cols-2 sm:grid-cols-5 gap-6">
          {STEPS.map((s) => (
            <div key={s.n}>
              <p className="font-mono text-xs text-sage mb-1">{s.n}</p>
              <p className="text-sm text-ink leading-snug">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 py-14">
        {/* Control toolbar */}
        <form onSubmit={onSubmit} className="bg-panel border border-line rounded-2xl p-7 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-[1.3fr_0.9fr_1fr_1.3fr] gap-8">
            <div>
              <label className="block font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
                Occasion
              </label>
              <div className="flex flex-wrap gap-2">
                {OCCASIONS.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setOccasion(o.value)}
                    className={`px-3.5 py-2 rounded-full border text-sm transition-colors ${
                      occasion === o.value
                        ? "bg-charcoal border-charcoal text-cream"
                        : "border-line text-muted hover:border-ink"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
                Gender
              </label>
              <div className="flex gap-2">
                {GENDERS.map((g) => (
                  <button
                    key={g.value}
                    type="button"
                    onClick={() => setGender(g.value)}
                    className={`flex-1 px-3 py-2 rounded-full border text-sm transition-colors ${
                      gender === g.value
                        ? "bg-charcoal border-charcoal text-cream"
                        : "border-line text-muted hover:border-ink"
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
              <label className="block font-mono text-[11px] tracking-widest text-muted uppercase mb-2 mt-5">
                City (optional)
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Barcelona, Spain"
                className="w-full bg-cream border border-line rounded-md px-3 py-2 text-sm text-ink placeholder:text-muted/60"
              />
            </div>

            <div>
              <label className="block font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
                Days to go
              </label>
              <div className="bg-cream border border-line rounded-lg px-5 py-4">
                <span className="font-display text-4xl text-ink tabular-nums">
                  {String(daysUntil).padStart(2, "0")}
                </span>
                <input
                  type="range"
                  min="1"
                  max="14"
                  value={daysUntil}
                  onChange={(e) => setDaysUntil(Number(e.target.value))}
                  className="w-full accent-ink mt-3"
                />
              </div>
            </div>

            <div>
              <label className="block font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
                Picture
              </label>
              {!previewUrl ? (
                <input type="file" accept="image/*" onChange={onSelfieChange} className="text-xs text-muted" />
              ) : (
                <div className="flex items-center gap-3">
                  <img src={previewUrl} alt="Selfie preview" className="w-16 h-16 object-cover rounded-md border border-line" />
                  <button
                    type="button"
                    onClick={() => {
                      setSelfie(null);
                      setPreviewUrl(null);
                    }}
                    className="text-xs text-muted underline"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between mt-6 pt-6 border-t border-line">
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="ml-auto bg-charcoal text-cream font-medium rounded-full px-8 py-3 disabled:opacity-50 hover:brightness-125 transition"
            >
              {loading ? "Building…" : "Build my countdown"}
            </button>
          </div>
        </form>

        {/* Live log */}
        {log.length > 0 && loading && (
          <div className="bg-panel border border-line rounded-2xl p-5 font-mono text-sm mb-8">
            <p className="text-muted text-xs uppercase tracking-widest mb-3">System log</p>
            <div className="flex flex-wrap gap-x-6 gap-y-1.5">
              {log.map((line, i) => (
                <p key={i} className="text-ink/80">
                  <span className="text-sage">›</span> {line}
                </p>
              ))}
              <p className="text-sage">
                <span className="log-cursor">▍</span>
              </p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-10">
            <div className="bg-blush/50 border border-line rounded-2xl p-8">
              <h2 className="font-display italic text-3xl text-ink mb-2">{result.headline}</h2>
              <p className="text-muted max-w-2xl">{result.final_summary}</p>
              {result.weather_summary && (
                <p className="font-mono text-xs text-muted/70 mt-3">Forecast: {result.weather_summary}</p>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8 items-start">
              <div>
                <h3 className="font-mono text-xs tracking-widest text-muted uppercase mb-4">Skin plan</h3>
                <p className="text-muted text-sm mb-4 max-w-lg">{result.skin_summary}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                  {result.routine?.map((d) => (
                    <div key={d.day} className="border border-line rounded-xl px-4 py-4 bg-panel">
                      <p className="font-display text-ink mb-2">
                        Day {d.day} <span className="text-sage">·</span> {d.focus}
                      </p>
                      <ul className="list-disc list-inside text-muted text-sm space-y-1">
                        {d.actions.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-sagelight/60 border border-line rounded-2xl p-6">
                <h3 className="font-mono text-xs tracking-widest text-muted uppercase mb-1">
                  Color season: {result.color_season}
                </h3>
                <p className="text-muted text-sm mb-4">{result.color_reasoning}</p>
                <div className="flex gap-3 flex-wrap mb-6">
                  {result.color_palette?.map((hex) => (
                    <div key={hex} className="flex flex-col items-center gap-1.5">
                      <div className="w-10 h-10 rounded-full border border-line" style={{ backgroundColor: hex }} />
                      <span className="font-mono text-[10px] text-muted">{hex}</span>
                    </div>
                  ))}
                </div>

                <h3 className="font-mono text-xs tracking-widest text-muted uppercase mb-4">
                  Outfit picks (color-verified)
                </h3>
                <div className="grid grid-cols-1 gap-5">
                  {result.accepted_outfits?.map((o, i) => (
                    <div
                      key={i}
                      className="group border border-line rounded-2xl overflow-hidden bg-panel transition-all hover:shadow-lg"
                    >
                      {o.result_image_url ? (
                        <img
                          src={o.result_image_url}
                          alt={o.label}
                          className="w-full aspect-[3/4] object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                        />
                      ) : (
                        <div className="w-full aspect-[3/4] bg-sagelight flex items-center justify-center text-muted text-sm">
                          Preview unavailable
                        </div>
                      )}
                      <div className="p-4">
                        <div className="flex items-center justify-between">
                          <p className="font-display text-ink text-lg">{o.label}</p>
                          {o.dominant_color && (
                            <div
                              className="w-4 h-4 rounded-full border border-line shrink-0 ml-2"
                              title={`Dominant color: ${o.dominant_color}`}
                              style={{ backgroundColor: o.dominant_color }}
                            />
                          )}
                        </div>
                        <p className="text-muted text-sm mt-1.5 leading-relaxed">{o.reasoning}</p>
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-line">
                          {o.match_score != null ? (
                            <p className="font-mono text-muted/70 text-xs">
                              {o.match_score} {o.verified ? "✓ verified" : "(best available)"}
                              {o.color_confidence && <span title="Color confirmed by both the rendered photo and the original reference photo"> · 2x-checked</span>}
                            </p>
                          ) : (
                            <span />
                          )}
                          {o.shop_url && (
                            <a
                              href={o.shop_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-mono text-xs text-ink hover:underline"
                            >
                              Shop this look →
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
