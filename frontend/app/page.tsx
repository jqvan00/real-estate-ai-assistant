"use client";

import { useMemo, useState, type ReactNode } from "react";
import LoanCalculator from "./LoanCalculator";
import VoiceChat from "./VoiceChat";

type SourceBreakdownItem = {
  name?: string;
  type?: string;
  confidence?: number;
};

type PriceHistoryItem = {
  date: string;
  event: string;
  price: number;
  dollarChange: number | null;
  percentChange: number | null;
  direction: string;
};

type AnalyzeApiResponse = {
  property_id: number;
  address: string;
  verified_profile: Record<string, unknown>;
  analysis: {
    briefing?: string;
    highlights?: string[];
    next_step?: string;
    comps?: {
      count?: number;
    };
    [key: string]: unknown;
  };
  source_breakdown: {
    sources?: SourceBreakdownItem[];
  };
};

type PropertyView = {
  address: string;
  listingUrl: string;
  beds: number;
  baths: number;
  sqft: number;
  yearBuilt: number;
  lotSize: string;
  market: {
    listingPrice: number;
    estimatedValue: number;
    nearby1Mile: number;
    nearby3Mile: number;
    nearby5Mile: number;
    nearby1MileCount: number;
    nearby3MileCount: number;
    nearby5MileCount: number;
    nearbyMetric: string;
    valueVsMarket: string;
  };
  verified: {
    formattedAddress: string;
    latitude: number | string | null;
    longitude: number | string | null;
    county: string;
    state: string;
    zipCode: string;
    propertyType: string;
    listingStatus: string;
    source: string;
    taxYear: number | null;
    taxTotal: number | null;
    listingSource: string;
    mlsNumber: string;
    daysOnZillow: number | null;
    listedDate: string;
    lastPriceChangeDate: string;
    lastPricePrevious: number | null;
    lastPriceCurrent: number | null;
    lastPriceChangePercent: number | null;
    lastPriceChangeDirection: string;
  };
  overview: string;
  listingDescriptionSummary: string;
  aiSummary: string;
  aiHighlights: string[];
  schools: string[];
  amenities: string[];
  priceHistory: PriceHistoryItem[];
  sourceBreakdown: SourceBreakdownItem[];
  propertyId: number | null;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const blankProperty: PropertyView = {
  address: "",
  listingUrl: "",
  beds: 0,
  baths: 0,
  sqft: 0,
  yearBuilt: 0,
  lotSize: "",
  market: {
    listingPrice: 0,
    estimatedValue: 0,
    nearby1Mile: 0,
    nearby3Mile: 0,
    nearby5Mile: 0,
    nearby1MileCount: 0,
    nearby3MileCount: 0,
    nearby5MileCount: 0,
    nearbyMetric: "median comparable value",
    valueVsMarket: "Market data unavailable",
  },
  verified: {
    formattedAddress: "",
    latitude: null,
    longitude: null,
    county: "",
    state: "",
    zipCode: "",
    propertyType: "",
    listingStatus: "",
    source: "",
    taxYear: null,
    taxTotal: null,
    listingSource: "",
    mlsNumber: "",
    daysOnZillow: null,
    listedDate: "",
    lastPriceChangeDate: "",
    lastPricePrevious: null,
    lastPriceCurrent: null,
    lastPriceChangePercent: null,
    lastPriceChangeDirection: "",
  },
  overview: "",
  listingDescriptionSummary: "",
  aiSummary: "",
  aiHighlights: [],
  schools: [],
  amenities: [],
  priceHistory: [],
  sourceBreakdown: [],
  propertyId: null,
};

function money(value: number) {
  if (!Number.isFinite(value) || value <= 0) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function parseDisplayDate(value: string) {
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (dateOnly) {
    return new Date(
      Number(dateOnly[1]),
      Number(dateOnly[2]) - 1,
      Number(dateOnly[3])
    );
  }
  return new Date(value);
}

function displayDate(value: string) {
  if (!value) return "N/A";
  const date = parseDisplayDate(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function displayListedDate(value: string, fallbackDays: number | null) {
  if (!value) {
    return fallbackDays === null
      ? "N/A"
      : `Date unavailable (${fallbackDays} day${fallbackDays === 1 ? "" : "s"})`;
  }

  const listedDate = parseDisplayDate(value);
  if (Number.isNaN(listedDate.getTime())) return value;

  const today = new Date();
  const listedUtc = Date.UTC(
    listedDate.getFullYear(),
    listedDate.getMonth(),
    listedDate.getDate()
  );
  const todayUtc = Date.UTC(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
  );
  const elapsedDays = Math.max(
    0,
    Math.floor((todayUtc - listedUtc) / 86_400_000)
  );

  return `${displayDate(value)} (${elapsedDays} day${
    elapsedDays === 1 ? "" : "s"
  })`;
}

function displayPriceChange(
  previousPrice: number | null,
  currentPrice: number | null,
  percent: number | null,
  direction: string,
  date: string
) {
  if (previousPrice && currentPrice && percent !== null && direction) {
    const dateText = date ? ` · ${displayDate(date)}` : "";
    return `${money(previousPrice)} → ${money(currentPrice)} (${percent.toFixed(
      1
    )}% ${direction})${dateText}`;
  }
  if (currentPrice) {
    return `${money(currentPrice)}${date ? ` · ${displayDate(date)}` : ""}`;
  }
  return "No recorded price change";
}

function summarizeListingDescription(value: unknown) {
  const description = toText(value).replace(/\s+/g, " ").trim();
  if (!description) return "";

  const sentences = description.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [
    description,
  ];
  const selectedSentences: string[] = [];
  let characterCount = 0;
  for (const sentence of sentences) {
    const cleaned = sentence.trim();
    if (!cleaned) continue;
    if (
      selectedSentences.length >= 4 ||
      (characterCount + cleaned.length > 650 && selectedSentences.length > 0)
    ) {
      break;
    }
    selectedSentences.push(cleaned);
    characterCount += cleaned.length;
  }
  return selectedSentences.join(" ");
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function marketPosition(listingPrice: number, estimatedValue: number) {
  if (listingPrice > 0 && estimatedValue > 0) {
    const difference = Math.abs(estimatedValue - listingPrice);
    const percent = Math.round((difference / estimatedValue) * 100);
    if (difference === 0) return "At estimated market value";
    return estimatedValue > listingPrice
      ? `${money(difference)} (${percent}%) below estimate`
      : `${money(difference)} (${percent}%) above estimate`;
  }
  if (estimatedValue > 0) return "Not actively listed";
  if (listingPrice > 0) return "Value estimate unavailable";
  return "Market data unavailable";
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return null;
}

function toText(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (value === null || value === undefined) return "";
  return String(value);
}

function Card({
  children,
  style,
}: {
  children: ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        borderRadius: 28,
        border: "1px solid rgba(255,255,255,0.10)",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))",
        boxShadow: "0 24px 80px rgba(0,0,0,0.35)",
        backdropFilter: "blur(18px)",
        WebkitBackdropFilter: "blur(18px)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function SectionTitle({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: "-0.02em" }}>
        {title}
      </div>
      {subtitle ? (
        <div
          style={{
            marginTop: 6,
            fontSize: 13,
            color: "rgba(255,255,255,0.55)",
            lineHeight: 1.6,
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </div>
  );
}

function LabelValue({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        borderRadius: 20,
        padding: 16,
        border: "1px solid rgba(255,255,255,0.10)",
        background: "rgba(0,0,0,0.30)",
      }}
    >
      <div
        style={{
          fontSize: 13,
          color: "rgba(255,255,255,0.55)",
          marginBottom: 8,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800 }}>{value}</div>
    </div>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        borderRadius: 999,
        border: "1px solid rgba(255,255,255,0.10)",
        background: "rgba(0,0,0,0.30)",
        padding: "8px 12px",
        fontSize: 13,
        color: "rgba(255,255,255,0.82)",
      }}
    >
      {children}
    </div>
  );
}

function buildPropertyView(
  data: AnalyzeApiResponse,
  current: PropertyView,
  requestedAddress: string,
  requestedListingUrl: string
): PropertyView {
  const v = data?.verified_profile || {};
  const analysis = data?.analysis || {};
  const sources = data?.source_breakdown?.sources || [];

  const formattedAddress =
    toText(v.formatted_address) ||
    toText(v.address) ||
    requestedAddress ||
    current.address;

  const bedrooms = toNumber(v.bedrooms) ?? current.beds;
  const bathrooms = toNumber(v.bathrooms) ?? current.baths;
  const sqft = toNumber(v.square_footage) ?? current.sqft;
  const yearBuilt = toNumber(v.year_built) ?? current.yearBuilt;
  const listingPrice = toNumber(v.listing_price) ?? current.market.listingPrice;
  // This card is intentionally ZillAPI's Zestimate only. Do not carry an
  // estimate from the previously viewed property when the field is unavailable.
  const estimatedValue = toNumber(v.estimated_value) ?? 0;

  const nearby1 = toNumber(v.nearby_1_mile) ?? current.market.nearby1Mile;
  const nearby3 = toNumber(v.nearby_3_mile) ?? current.market.nearby3Mile;
  const nearby5 = toNumber(v.nearby_5_mile) ?? current.market.nearby5Mile;
  const nearby1Count =
    toNumber(v.nearby_1_mile_count) ?? current.market.nearby1MileCount;
  const nearby3Count =
    toNumber(v.nearby_3_mile_count) ?? current.market.nearby3MileCount;
  const nearby5Count =
    toNumber(v.nearby_5_mile_count) ?? current.market.nearby5MileCount;
  const nearbyMetric =
    toText(v.nearby_metric) || current.market.nearbyMetric;

  const valueVsMarket = marketPosition(listingPrice, estimatedValue);

  const propertyType = toText(v.property_type) || current.verified.propertyType;
  const listingStatus = toText(v.listing_status) || current.verified.listingStatus;
  const latitude = toNumber(v.latitude) ?? current.verified.latitude;
  const longitude = toNumber(v.longitude) ?? current.verified.longitude;
  const county = toText(v.county) || current.verified.county;
  const state = toText(v.state) || current.verified.state;
  const zipCode = toText(v.zip_code) || toText(v.zipCode) || current.verified.zipCode;

  const briefing = toText(analysis.briefing) || current.aiSummary;
  const highlights =
    Array.isArray(analysis.highlights) && analysis.highlights.length > 0
      ? analysis.highlights.map((h) => toText(h)).filter(Boolean)
      : current.aiHighlights;
  const schools =
    Array.isArray(analysis.schools) && analysis.schools.length > 0
      ? analysis.schools.map((s) => toText(s)).filter(Boolean)
      : current.schools;
  const priceHistory = Array.isArray(v.price_history)
    ? v.price_history
        .map((item): PriceHistoryItem | null => {
          if (!item || typeof item !== "object") return null;
          const row = item as Record<string, unknown>;
          const price = toNumber(row.price);
          if (price === null) return null;
          return {
            date: toText(row.date),
            event: toText(row.event) || "Price event",
            price,
            dollarChange: toNumber(row.dollar_change),
            percentChange: toNumber(row.percent_change),
            direction: toText(row.direction),
          };
        })
        .filter((item): item is PriceHistoryItem => item !== null)
    : [];

  return {
    ...current,
    address: formattedAddress,
    listingUrl: requestedListingUrl || current.listingUrl,
    beds: bedrooms,
    baths: bathrooms,
    sqft,
    yearBuilt,
    lotSize: toText(v.lot_size) || current.lotSize,
    market: {
      listingPrice,
      estimatedValue,
      nearby1Mile: nearby1,
      nearby3Mile: nearby3,
      nearby5Mile: nearby5,
      nearby1MileCount: nearby1Count,
      nearby3MileCount: nearby3Count,
      nearby5MileCount: nearby5Count,
      nearbyMetric,
      valueVsMarket,
    },
    verified: {
      formattedAddress,
      latitude,
      longitude,
      county,
      state,
      zipCode,
      propertyType,
      listingStatus,
      source: toText(v.source) || "census_geocoder + rentcast",
      taxYear: toNumber(v.tax_year) ?? current.verified.taxYear,
      taxTotal: toNumber(v.tax_total) ?? current.verified.taxTotal,
      listingSource:
        toText(v.listing_source) || current.verified.listingSource,
      mlsNumber: toText(v.mls_number) || current.verified.mlsNumber,
      daysOnZillow:
        toNumber(v.days_on_market) ?? null,
      listedDate: toText(v.listed_date),
      lastPriceChangeDate:
        toText(v.last_price_change_date),
      lastPricePrevious: toNumber(v.last_price_previous),
      lastPriceCurrent: toNumber(v.last_price_current),
      lastPriceChangePercent: toNumber(v.last_price_change_percent),
      lastPriceChangeDirection: toText(v.last_price_change_direction),
    },
    overview: formattedAddress ? `Verified location: ${formattedAddress}` : "",
    listingDescriptionSummary: summarizeListingDescription(
      v.listing_description
    ),
    aiSummary: briefing,
    aiHighlights: highlights,
    schools: schools,
    priceHistory,
    sourceBreakdown: sources,
    propertyId: data.property_id ?? current.propertyId,
  };
}

export default function Page() {
  const [searchAddress, setSearchAddress] = useState("");
  const [listingUrl, setListingUrl] = useState("");
  const [selected, setSelected] = useState<PropertyView>(blankProperty);
  const [loading, setLoading] = useState(false);
  const [comparablesLoading, setComparablesLoading] = useState(false);
  const [comparablesRequested, setComparablesRequested] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [activeTab, setActiveTab] = useState<
    "summary" | "assistant" | "affordability"
  >("summary");

  const marketCards = useMemo(
    () => {
      const comparableLabel =
        selected.market.nearbyMetric === "CMA-style indicated value"
          ? "CMA Indicated Value"
          : "Median Comparable Value";
      return [
      { label: "Listing Price", value: money(selected.market.listingPrice) },
      { label: "Zestimate", value: money(selected.market.estimatedValue) },
      {
        label: "Listed",
        value: displayListedDate(
          selected.verified.listedDate,
          selected.verified.daysOnZillow
        ),
      },
      {
        label: "Latest Price Change",
        value: displayPriceChange(
          selected.verified.lastPricePrevious,
          selected.verified.lastPriceCurrent,
          selected.verified.lastPriceChangePercent,
          selected.verified.lastPriceChangeDirection,
          selected.verified.lastPriceChangeDate
        ),
      },
      {
        label: `${comparableLabel} · 1 Mile (${selected.market.nearby1MileCount} comps)`,
        value: money(selected.market.nearby1Mile),
      },
      {
        label: `${comparableLabel} · 3 Miles (${selected.market.nearby3MileCount} comps)`,
        value: money(selected.market.nearby3Mile),
      },
      {
        label: `${comparableLabel} · 5 Miles (${selected.market.nearby5MileCount} comps)`,
        value: money(selected.market.nearby5Mile),
      },
      { label: "Market Position", value: selected.market.valueVsMarket },
    ];
    },
    [selected]
  );

  const maxValue = Math.max(
    selected.market.listingPrice,
    selected.market.estimatedValue,
    selected.market.nearby1Mile,
    selected.market.nearby3Mile,
    selected.market.nearby5Mile,
    1
  );

  async function runSearch() {
    const addressToSearch = searchAddress.trim();
    const urlToSearch = listingUrl.trim();

    // Need either an address OR a listing URL
    if (!addressToSearch && !urlToSearch) {
      setError("Please enter an address or listing URL.");
      return;
    }

    setLoading(true);
    setError("");

    setSelected((current) => ({
      ...current,
      address: addressToSearch || "Extracting from URL...",
      listingUrl: urlToSearch || current.listingUrl,
    }));

    try {
      const response = await fetch(`${API_BASE_URL}/properties/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          address: addressToSearch || "",  // Can be empty if URL provided
          listing_url: urlToSearch || null,
          include_comparables: false,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Property analyze request failed");
      }

      const data = (await response.json()) as AnalyzeApiResponse;

      setSelected((current) =>
        buildPropertyView(data, current, addressToSearch || "From URL", urlToSearch)
      );
      setSearchAddress(
        toText(data?.verified_profile?.formatted_address) || addressToSearch
      );
      setLastUpdated(new Date().toLocaleString());
      setComparablesRequested(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function loadComparables() {
    if (!selected.propertyId) {
      setError("Search for a property before loading comparables.");
      return;
    }

    setComparablesLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/properties/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          address: searchAddress.trim() || selected.address,
          listing_url: listingUrl.trim() || selected.listingUrl || null,
          include_comparables: true,
          max_comparables: 5,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Comparable lookup failed");
      }

      const data = (await response.json()) as AnalyzeApiResponse;
      setSelected((current) =>
        buildPropertyView(
          data,
          current,
          searchAddress.trim() || selected.address,
          listingUrl.trim() || selected.listingUrl
        )
      );
      setComparablesRequested(true);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparable lookup failed");
    } finally {
      setComparablesLoading(false);
    }
  }

  function resetView() {
    setSearchAddress("");
    setListingUrl("");
    setSelected(blankProperty);
    setError("");
    setLastUpdated("");
    setComparablesRequested(false);
    setActiveTab("summary");
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left, rgba(34,211,238,0.14), transparent 28%), radial-gradient(circle at top right, rgba(139,92,246,0.12), transparent 26%), linear-gradient(180deg, #040510 0%, #050816 46%, #02030a 100%)",
        color: "white",
      }}
    >
      <div style={{ maxWidth: 1440, margin: "0 auto", padding: 24 }}>
        <div
          role="tablist"
          aria-label="Property workspace"
          style={{
            display: "inline-flex",
            gap: 6,
            marginBottom: 18,
            padding: 6,
            borderRadius: 18,
            border: "1px solid rgba(255,255,255,0.10)",
            background: "rgba(0,0,0,0.28)",
          }}
        >
          {[
            { id: "summary" as const, label: "Summary" },
            { id: "assistant" as const, label: "AI Assistant" },
            { id: "affordability" as const, label: "Affordability" },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: "11px 18px",
                  borderRadius: 13,
                  border: isActive
                    ? "1px solid rgba(34,211,238,0.32)"
                    : "1px solid transparent",
                  background: isActive
                    ? "linear-gradient(135deg, rgba(34,211,238,0.18), rgba(139,92,246,0.18))"
                    : "transparent",
                  color: isActive ? "#fff" : "rgba(255,255,255,0.58)",
                  fontSize: 14,
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div
          style={{
            display: activeTab === "affordability" ? "none" : "block",
          }}
        >
          <Card>
            <div style={{ padding: 26 }}>
              <h1
                style={{
                  margin: "0 0 22px",
                  fontSize: "clamp(2rem, 4vw, 3.2rem)",
                  lineHeight: 1.04,
                  letterSpacing: "-0.05em",
                  maxWidth: 980,
                }}
              >
                Search a Property
              </h1>

              <div style={{ display: "grid", gap: 12 }}>
                <input
                  value={searchAddress}
                  onChange={(e) => setSearchAddress(e.target.value)}
                  placeholder="Search by address"
                  style={{
                    width: "100%",
                    borderRadius: 18,
                    border: "1px solid rgba(255,255,255,0.10)",
                    background: "rgba(0,0,0,0.45)",
                    color: "#fff",
                    outline: "none",
                    padding: "16px 18px",
                    fontSize: 15,
                  }}
                />
                <input
                  value={listingUrl}
                  onChange={(e) => setListingUrl(e.target.value)}
                  placeholder="Search by Zillow or listing URL"
                  style={{
                    width: "100%",
                    borderRadius: 18,
                    border: "1px solid rgba(255,255,255,0.10)",
                    background: "rgba(0,0,0,0.45)",
                    color: "#fff",
                    outline: "none",
                    padding: "16px 18px",
                    fontSize: 15,
                  }}
                />
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <button
                    onClick={runSearch}
                    disabled={loading}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "14px 20px",
                      borderRadius: 16,
                      background: loading ? "rgba(255,255,255,0.75)" : "#fff",
                      color: "#030712",
                      border: 0,
                      fontWeight: 900,
                      cursor: loading ? "not-allowed" : "pointer",
                    }}
                  >
                    {loading ? "Analyzing..." : "Analyze Property"}
                  </button>
                  <button
                    onClick={resetView}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "14px 20px",
                      borderRadius: 16,
                      background: "rgba(255,255,255,0.05)",
                      color: "#fff",
                      border: "1px solid rgba(255,255,255,0.10)",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>

            <div
              style={{
                display: activeTab === "summary" ? "block" : "none",
                padding: "0 26px 26px",
              }}
            >
              <div
                style={{
                  display: "grid",
                  gap: 12,
                  gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                }}
              >
                <LabelValue label="Beds" value={String(selected.beds)} />
                <LabelValue label="Baths" value={String(selected.baths)} />
                <LabelValue
                  label="Sq Ft"
                  value={selected.sqft.toLocaleString()}
                />
                <LabelValue
                  label="Year Built"
                  value={selected.yearBuilt > 0 ? String(selected.yearBuilt) : "N/A"}
                />
              </div>

              <div
                style={{
                  marginTop: 22,
                  paddingTop: 22,
                  borderTop: "1px solid rgba(255,255,255,0.10)",
                }}
              >
                <SectionTitle
                  title="Market Snapshot"
                  subtitle={
                    selected.verified.listingSource
                      ? `Active listing via ${selected.verified.listingSource}${
                          selected.verified.mlsNumber
                            ? ` · MLS #${selected.verified.mlsNumber}`
                            : ""
                        }`
                      : "Listing price and local value comparison"
                  }
                />
                <div
                  style={{
                    display: "grid",
                    gap: 12,
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(210px, 1fr))",
                  }}
                >
                  {marketCards.map((card) => (
                    <LabelValue
                      key={card.label}
                      label={card.label}
                      value={card.value}
                    />
                  ))}
                </div>
              </div>

              <div
                style={{
                  marginTop: 22,
                  paddingTop: 22,
                  borderTop: "1px solid rgba(255,255,255,0.10)",
                }}
              >
                <SectionTitle
                  title="Property Tax Information"
                  subtitle="Annual tax assessment"
                />
                <div
                  style={{
                    display: "grid",
                    gap: 12,
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(200px, 1fr))",
                  }}
                >
                  <LabelValue
                    label="Tax Year"
                    value={selected.verified.taxYear?.toString() || "N/A"}
                  />
                  <LabelValue
                    label="Annual Tax"
                    value={
                      selected.verified.taxTotal
                        ? money(selected.verified.taxTotal)
                        : "N/A"
                    }
                  />
                  <LabelValue
                    label="County"
                    value={selected.verified.county || "N/A"}
                  />
                  <LabelValue
                    label="Property Type"
                    value={selected.verified.propertyType || "N/A"}
                  />
                </div>
              </div>

              <div
                style={{
                  marginTop: 22,
                  paddingTop: 22,
                  borderTop: "1px solid rgba(255,255,255,0.10)",
                }}
              >
                <SectionTitle
                  title="Listing Description Summary"
                  subtitle="Condensed from the listing remarks provided by ZillAPI"
                />
                <div
                  style={{
                    borderRadius: 20,
                    padding: 18,
                    border: "1px solid rgba(255,255,255,0.10)",
                    background: "rgba(0,0,0,0.28)",
                    color: selected.listingDescriptionSummary
                      ? "rgba(255,255,255,0.82)"
                      : "rgba(255,255,255,0.50)",
                    fontSize: 15,
                    lineHeight: 1.75,
                  }}
                >
                  {selected.listingDescriptionSummary ||
                    "No listing description is available from ZillAPI for this property."}
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div
          style={{
            marginTop: 18,
            display: activeTab === "summary" ? "grid" : "none",
            gap: 18,
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          }}
        >
          <Card>
            <div style={{ padding: 22 }}>
              <SectionTitle
                title="Nearby Schools"
                subtitle="Nearest named schools · straight-line distance"
              />
              <div style={{ display: "grid", gap: 10 }}>
                {selected.schools.length > 0 ? (
                  selected.schools.map((school) => (
                    <div
                      key={school}
                      style={{
                        borderRadius: 18,
                        padding: 14,
                        border: "1px solid rgba(255,255,255,0.10)",
                        background: "rgba(0,0,0,0.28)",
                        fontSize: 14,
                      }}
                    >
                      {school}
                    </div>
                  ))
                ) : (
                  <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 14 }}>
                    School data not available
                  </div>
                )}
              </div>
            </div>
          </Card>

          <Card>
            <div style={{ padding: 22 }}>
              <SectionTitle
                title="Nearby Value Comparison"
                subtitle={
                  comparablesRequested
                    ? "Optional CMA-style analysis of recently sold ZillAPI records"
                    : "CMA records are not loaded automatically"
                }
              />
              <div
                style={{
                  marginBottom: 16,
                  padding: 14,
                  borderRadius: 18,
                  border: "1px solid rgba(250,204,21,0.24)",
                  background: "rgba(250,204,21,0.07)",
                  color: "rgba(255,255,255,0.76)",
                  fontSize: 13,
                  lineHeight: 1.6,
                }}
              >
                <div>
                  Running the CMA may use up to 5 ZillAPI credits. The analysis
                  ranks sold records by proximity, recency, square footage,
                  bedrooms, bathrooms, and age, then compares price per square
                  foot. It is optional and never runs during a normal property
                  search.
                </div>
                <button
                  type="button"
                  onClick={loadComparables}
                  disabled={!selected.propertyId || comparablesLoading}
                  style={{
                    marginTop: 12,
                    padding: "11px 16px",
                    borderRadius: 14,
                    border: 0,
                    background:
                      !selected.propertyId || comparablesLoading
                        ? "rgba(255,255,255,0.16)"
                        : "#facc15",
                    color:
                      !selected.propertyId || comparablesLoading
                        ? "rgba(255,255,255,0.45)"
                        : "#1c1917",
                    fontWeight: 900,
                    cursor:
                      !selected.propertyId || comparablesLoading
                        ? "not-allowed"
                        : "pointer",
                  }}
                >
                  {comparablesLoading
                    ? "Loading Comparables..."
                    : comparablesRequested
                    ? "Refresh CMA (up to 5 credits)"
                    : "Run CMA (up to 5 credits)"}
                </button>
              </div>
              {comparablesRequested &&
                selected.market.nearby5MileCount === 0 && (
                  <div
                    style={{
                      marginBottom: 14,
                      color: "rgba(255,255,255,0.58)",
                      fontSize: 13,
                    }}
                  >
                    ZillAPI returned no usable sold records with both a price
                    and location. This does not necessarily mean no nearby
                    sales exist.
                  </div>
                )}
              {[
                [
                  "1 Mile Radius",
                  selected.market.nearby1Mile,
                  selected.market.nearby1MileCount,
                ],
                [
                  "3 Mile Radius",
                  selected.market.nearby3Mile,
                  selected.market.nearby3MileCount,
                ],
                [
                  "5 Mile Radius",
                  selected.market.nearby5Mile,
                  selected.market.nearby5MileCount,
                ],
              ].map(([label, value, count]) => {
                const pct = Math.round((Number(value) / maxValue) * 100);
                return (
                  <div
                    key={label}
                    style={{
                      marginBottom: 14,
                      borderRadius: 20,
                      padding: 14,
                      border: "1px solid rgba(255,255,255,0.10)",
                      background: "rgba(0,0,0,0.28)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        color: "rgba(255,255,255,0.58)",
                        fontSize: 13,
                      }}
                    >
                      <span>
                        {label} · {count} comparable{Number(count) === 1 ? "" : "s"}
                      </span>
                      <span>{money(Number(value))}</span>
                    </div>
                    <div
                      style={{
                        marginTop: 10,
                        height: 10,
                        borderRadius: 999,
                        background: "rgba(255,255,255,0.08)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${clamp(pct, 12, 100)}%`,
                          height: "100%",
                          borderRadius: 999,
                          background: "linear-gradient(90deg, #22d3ee, #8b5cf6)",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        <div
          style={{
            display: activeTab === "summary" ? "block" : "none",
            marginTop: 18,
          }}
        >
          <Card>
            <div style={{ padding: 22 }}>
              <SectionTitle
                title="Price History"
                subtitle="Recorded listing events and price movements from ZillAPI"
              />
              <div style={{ display: "grid", gap: 10 }}>
                {selected.priceHistory.length > 0 ? (
                  selected.priceHistory.map((entry, index) => {
                    const changeColor =
                      entry.direction === "increase"
                        ? "#86efac"
                        : entry.direction === "decrease"
                        ? "#fca5a5"
                        : "rgba(255,255,255,0.62)";
                    const changePrefix =
                      entry.dollarChange !== null && entry.dollarChange > 0
                        ? "+"
                        : "";
                    return (
                      <div
                        key={`${entry.date}-${entry.event}-${index}`}
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "minmax(120px, 0.8fr) minmax(150px, 1.2fr) minmax(120px, 0.8fr) minmax(160px, 1fr)",
                          gap: 14,
                          alignItems: "center",
                          borderRadius: 18,
                          padding: 14,
                          border: "1px solid rgba(255,255,255,0.10)",
                          background: "rgba(0,0,0,0.28)",
                        }}
                      >
                        <div style={{ color: "rgba(255,255,255,0.62)" }}>
                          {displayDate(entry.date)}
                        </div>
                        <div style={{ fontWeight: 800 }}>{entry.event}</div>
                        <div style={{ fontWeight: 900 }}>
                          {money(entry.price)}
                        </div>
                        <div style={{ color: changeColor, fontWeight: 800 }}>
                          {entry.dollarChange !== null
                            ? `${changePrefix}${
                                entry.dollarChange < 0 ? "-" : ""
                              }${money(Math.abs(entry.dollarChange))}${
                                entry.percentChange !== null
                                  ? ` (${entry.percentChange.toFixed(1)}% ${
                                      entry.direction
                                    })`
                                  : ""
                              }`
                            : "Initial listing"}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div
                    style={{
                      borderRadius: 18,
                      padding: 16,
                      border: "1px solid rgba(255,255,255,0.10)",
                      background: "rgba(0,0,0,0.28)",
                      color: "rgba(255,255,255,0.55)",
                    }}
                  >
                    No price-history events are available from ZillAPI for this
                    property.
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>







        {/* Voice & Chat Section */}
        <div
          style={{
            display: activeTab === "assistant" ? "block" : "none",
            marginTop: 18,
          }}
        >
          <VoiceChat propertyId={selected.propertyId} />
        </div>

        <div
          style={{
            display: activeTab === "affordability" ? "block" : "none",
            marginTop: 18,
          }}
        >
          <LoanCalculator
            propertyPrice={selected.market.listingPrice}
            annualPropertyTax={selected.verified.taxTotal}
            propertyState={selected.verified.state}
            propertyCounty={selected.verified.county}
          />
        </div>

        {error ? (
          <div
            style={{
              marginTop: 18,
              borderRadius: 18,
              padding: 16,
              border: "1px solid rgba(239,68,68,0.35)",
              background: "rgba(127,29,29,0.24)",
              color: "#fecaca",
              fontSize: 14,
            }}
          >
            {error}
          </div>
        ) : null}
      </div>
    </main>
  );
}
