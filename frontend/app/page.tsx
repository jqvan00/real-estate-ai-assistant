"use client";

import { useMemo, useState } from "react";

type AnalyzeResponse = {
  property_id: number;
  address: string;
  verified_profile: {
    address: string;
    listing_url?: string | null;
    property_type?: string;
    beds?: number | null;
    baths?: number | null;
    sqft?: number | null;
    lot_size_acres?: number | null;
    year_built?: number | null;
    estimated_value?: number | null;
    annual_taxes?: number | null;
    school_names?: string[];
    nearby_places?: string[];
    flood_risk?: string;
    source_count?: number;
  };
  analysis: {
    briefing?: string;
    investment_snapshot?: {
      estimated_monthly_payment?: number | null;
      estimated_rent?: number | null;
      cap_rate_estimate?: number | null;
      note?: string;
    };
    schools?: string[];
    flood_zone?: string;
    nearby_places?: string[];
    commute?: Record<string, unknown>;
    neighborhood?: Record<string, unknown>;
    price_history?: { year: number; value: number | null }[];
    renovation_value?: Record<string, unknown>;
    voice_prompt?: string;
    pdf_report?: { status?: string; file_name?: string };
    sources_used?: string[];
  };
  source_breakdown: {
    sources: { name?: string; type?: string; confidence?: number }[];
  };
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [address, setAddress] = useState("");
  const [listingUrl, setListingUrl] = useState("");
  const [chatMessage, setChatMessage] = useState("What stands out about this home?");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [chatReply, setChatReply] = useState<string>("");
  const [chatConversationId, setChatConversationId] = useState<number | null>(null);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState("");

  const verified = result?.verified_profile;
  const analysis = result?.analysis;
  const sources = result?.source_breakdown.sources || [];

  const verifiedFacts = useMemo(() => {
    if (!verified) return [];
    return [
      ["Property type", verified.property_type ?? "Unknown"],
      ["Beds", verified.beds ?? "Unknown"],
      ["Baths", verified.baths ?? "Unknown"],
      ["Sqft", verified.sqft ?? "Unknown"],
      ["Lot size", verified.lot_size_acres ? `${verified.lot_size_acres} acres` : "Unknown"],
      ["Year built", verified.year_built ?? "Unknown"],
      ["Estimated value", verified.estimated_value ? `$${verified.estimated_value.toLocaleString()}` : "Unknown"],
      ["Annual taxes", verified.annual_taxes ? `$${verified.annual_taxes.toLocaleString()}` : "Unknown"],
      ["Flood risk", verified.flood_risk ?? "Unknown"],
      ["Source count", verified.source_count ?? 0],
    ];
  }, [verified]);

  async function analyzeProperty() {
    setLoadingAnalyze(true);
    setError("");
    setChatReply("");
    setChatConversationId(null);

    try {
      const response = await fetch(`${apiBase}/properties/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          address: address || listingUrl,
          listing_url: listingUrl || null,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Analyze request failed");
      }

      const data = (await response.json()) as AnalyzeResponse;
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoadingAnalyze(false);
    }
  }

  async function sendChat() {
    if (!result) return;
    setLoadingChat(true);
    setError("");

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          property_id: result.property_id,
          message: chatMessage,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Chat request failed");
      }

      const data = (await response.json()) as { reply: string; conversation_id: number | null };
      setChatReply(data.reply);
      setChatConversationId(data.conversation_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoadingChat(false);
    }
  }

  async function buildReport() {
    if (!result) return;
    setLoadingReport(true);
    setError("");

    try {
      const response = await fetch(`${apiBase}/reports/${result.property_id}`, {
        method: "POST",
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Report request failed");
      }

      const data = await response.json();
      setError(`Report saved: ${data.title}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoadingReport(false);
    }
  }

  return (
    <main className="container">
      <div className="topbar">
        <div className="badge">AI Real Estate Showing Assistant</div>
        <div className="small">Local demo mode · verified facts first</div>
      </div>

      <section className="hero">
        <h1>Analyze a property, see the facts, and ask follow-up questions.</h1>
        <p>
          This starter uses a multi-source property engine scaffold, a verified property profile,
          and clearly labeled AI analysis so the UI stays useful even before you plug in live APIs.
        </p>
      </section>

      <section className="grid two">
        <div className="card">
          <h2>Analyze property</h2>
          <div className="form">
            <div className="field">
              <label>Property address</label>
              <input
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="123 Main St, Bentonville, AR"
              />
            </div>

            <div className="field">
              <label>Listing URL</label>
              <input
                value={listingUrl}
                onChange={(e) => setListingUrl(e.target.value)}
                placeholder="https://www.zillow.com/..."
              />
            </div>

            <div className="actions">
              <button
                className="button primary"
                onClick={analyzeProperty}
                disabled={loadingAnalyze || (!address && !listingUrl)}
              >
                {loadingAnalyze ? "Analyzing..." : "Analyze Property"}
              </button>
              <button
                className="button secondary"
                onClick={() => {
                  setAddress("");
                  setListingUrl("");
                  setResult(null);
                  setChatReply("");
                  setChatConversationId(null);
                  setError("");
                }}
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Why this build is better</h2>
          <div className="stack">
            <div className="pill good">Multi-source engine scaffold</div>
            <div className="pill good">Verified facts separated from AI analysis</div>
            <div className="pill good">PDF report endpoint included</div>
            <div className="pill good">Chat and saved reports included</div>
            <div className="pill good">Mobile-friendly responsive layout</div>
          </div>
        </div>
      </section>

      {error ? (
        <section className="card" style={{ marginTop: 16 }}>
          <h2>Status</h2>
          <p className="small">{error}</p>
        </section>
      ) : null}

      {result ? (
        <section className="grid" style={{ marginTop: 16 }}>
          <div className="card">
            <h2>Verified facts</h2>
            <div className="grid three">
              {verifiedFacts.map(([label, value]) => (
                <div key={label as string} className="kpi">
                  <div className="label">{label}</div>
                  <div className="value">{String(value)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid two">
            <div className="card">
              <h2>AI briefing</h2>
              <p className="small">{analysis?.briefing ?? "No briefing available."}</p>
              <div style={{ height: 12 }} />
              <h3>Investment snapshot</h3>
              <div className="grid two">
                <div className="kpi">
                  <div className="label">Est. monthly payment</div>
                  <div className="value">
                    {analysis?.investment_snapshot?.estimated_monthly_payment
                      ? `$${analysis.investment_snapshot.estimated_monthly_payment.toLocaleString()}`
                      : "Unknown"}
                  </div>
                </div>
                <div className="kpi">
                  <div className="label">Est. rent</div>
                  <div className="value">
                    {analysis?.investment_snapshot?.estimated_rent
                      ? `$${analysis.investment_snapshot.estimated_rent.toLocaleString()}`
                      : "Unknown"}
                  </div>
                </div>
              </div>
              <p className="small">{analysis?.investment_snapshot?.note}</p>
            </div>

            <div className="card">
              <h2>Sources used</h2>
              <div className="pill-row">
                {sources.map((source, idx) => (
                  <span key={`${source.name ?? "source"}-${idx}`} className="pill">
                    {source.name ?? "Unknown"} · {(source.confidence ?? 0.5).toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="grid three">
            <div className="card">
              <h2>Schools</h2>
              <div className="stack">
                {(analysis?.schools ?? []).map((school) => (
                  <div key={school} className="pill">{school}</div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2>Nearby places</h2>
              <div className="stack">
                {(analysis?.nearby_places ?? []).map((place) => (
                  <div key={place} className="pill">{place}</div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2>Neighborhood</h2>
              <p className="small">{String(analysis?.neighborhood?.summary ?? "No neighborhood summary.")}</p>
              <div style={{ height: 8 }} />
              <p className="small">
                {String(analysis?.neighborhood?.market_position ?? "Market position not available.")}
              </p>
            </div>
          </div>

          <div className="grid two">
            <div className="card">
              <h2>Price history</h2>
              <pre>{JSON.stringify(analysis?.price_history ?? [], null, 2)}</pre>
            </div>

            <div className="card">
              <h2>Renovation upside</h2>
              <pre>{JSON.stringify(analysis?.renovation_value ?? {}, null, 2)}</pre>
            </div>
          </div>

          <div className="grid two">
            <div className="card">
              <h2>Ask a follow-up</h2>
              <div className="form">
                <div className="field">
                  <label>Question</label>
                  <textarea
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    placeholder="Ask about value, schools, flood risk, commute, or renovation upside..."
                  />
                </div>
                <div className="actions">
                  <button className="button primary" onClick={sendChat} disabled={loadingChat}>
                    {loadingChat ? "Thinking..." : "Send to Chat"}
                  </button>
                  <button className="button secondary" onClick={buildReport} disabled={loadingReport}>
                    {loadingReport ? "Saving..." : "Build Report"}
                  </button>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Chat response</h2>
              <p className="small">
                {chatReply || "No chat response yet. Ask a follow-up about the property."}
              </p>
              <div style={{ height: 10 }} />
              <h3>Conversation ID</h3>
              <p className="small">{chatConversationId ?? "Not started"}</p>
              <div style={{ height: 10 }} />
              <h3>Voice mode</h3>
              <p className="small">{analysis?.voice_prompt ?? "Voice prompt not ready."}</p>
            </div>
          </div>

          <div className="card">
            <h2>API notes</h2>
            <div className="grid two">
              <div>
                <h3>Endpoint coverage</h3>
                <ul className="small">
                  <li>POST /properties/analyze</li>
                  <li>GET /properties/{`{id}`}</li>
                  <li>POST /properties/{`{id}`}/refresh</li>
                  <li>POST /chat</li>
                  <li>GET /reports/{`{id}`}</li>
                  <li>GET /reports/{`{id}`}/pdf</li>
                  <li>POST /documents/upload</li>
                  <li>GET /analysis/{`{id}`}/investment</li>
                  <li>GET /analysis/{`{id}`}/schools</li>
                  <li>GET /analysis/{`{id}`}/flood</li>
                  <li>GET /analysis/{`{id}`}/nearby</li>
                </ul>
              </div>
              <div>
                <h3>Notes</h3>
                <p className="small">
                  This starter runs without external credentials. The connectors produce deterministic
                  local demo data now, and you can swap in ATTOM, RentCast, Estated, Regrid, Maps,
                  Schools, FEMA, and NOAA integrations later.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}
