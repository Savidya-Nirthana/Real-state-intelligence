"use client";

import { useState, useRef, useEffect } from "react";

// ── Types ───────────────────────────────────────────────────────────────────
interface ChatResult {
  answer: string;
  mode_used: string;
  strategy_used: string | null;
  evidence_urls: string[];
  generation_time: number;
  cache_hit?: boolean;
  cache_source?: string;
  similarity_score?: number;
  matched_query?: string;
  confidence_initial?: number;
  confidence_final?: number;
  correction_applied?: boolean;
  docs_used?: number;
}

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  meta?: ChatResult;
  timestamp: Date;
}

const STRATEGIES = [
  { value: "", label: "All Strategies" },
  { value: "child", label: "🥇 Parent-Child" },
  { value: "fixed", label: "📏 Fixed-Size" },
  { value: "sliding", label: "🪟 Sliding Window" },
  { value: "semantic", label: "🧠 Semantic" },
  { value: "late_chunk_base", label: "⏳ Late Chunk" },
];

const MODES = [
  { value: "cag", label: "CAG", desc: "Cache-Augmented", icon: "⚡" },
  { value: "rag", label: "RAG", desc: "Retrieval-Augmented", icon: "🔍" },
  { value: "crag", label: "CRAG", desc: "Corrective RAG", icon: "🛡️" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function QueryDashboard() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [strategy, setStrategy] = useState("");
  const [mode, setMode] = useState("cag");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [query]);

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: query.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMsg.content,
          mode,
          strategy: strategy || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data: ChatResult = await res.json();

      const aiMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.answer,
        meta: data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setError(err.message || "Failed to connect to the API");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--background)" }}>
      {/* ── Header ────────────────────────────────────────────── */}
      <header
        className="shrink-0 flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "rgba(6,10,20,0.9)", backdropFilter: "blur(12px)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black"
            style={{ background: "linear-gradient(135deg, #4f7cff, #7c6ff7)", color: "#fff" }}
          >
            PL
          </div>
          <div>
            <h1 className="text-sm font-bold" style={{ color: "var(--foreground)" }}>
              PrimeLands Intelligence
            </h1>
            <p className="text-xs" style={{ color: "var(--muted)" }}>
              Query Dashboard — RAG · CAG · CRAG
            </p>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="flex items-center gap-1 p-1 rounded-xl" style={{ background: "var(--card)" }}>
          {MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setMode(m.value)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
              style={{
                background: mode === m.value ? "var(--accent-blue)" : "transparent",
                color: mode === m.value ? "#fff" : "var(--muted)",
              }}
              title={m.desc}
            >
              {m.icon} {m.label}
            </button>
          ))}
        </div>

        {/* Strategy selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium" style={{ color: "var(--muted)" }}>
            Chunking:
          </label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border outline-none transition-colors"
            style={{
              background: "var(--card)",
              borderColor: "var(--border)",
              color: "var(--foreground)",
            }}
          >
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* ── Messages area ────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && !loading && (
            <EmptyState onSuggestionClick={(q) => { setQuery(q); }} />
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading && <LoadingIndicator />}

          {error && (
            <div
              className="fade-up mx-auto max-w-xl p-4 rounded-xl border text-sm"
              style={{
                background: "rgba(244,63,94,0.08)",
                borderColor: "rgba(244,63,94,0.25)",
                color: "#fb7185",
              }}
            >
              <strong>Error:</strong> {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* ── Input bar ────────────────────────────────────────── */}
      <div className="shrink-0 px-4 pb-4 pt-2" style={{ background: "var(--background)" }}>
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto flex items-end gap-3 p-3 rounded-2xl border transition-colors"
          style={{
            background: "var(--card)",
            borderColor: loading ? "var(--accent-blue)" : "var(--border)",
          }}
        >
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about PrimeLands properties..."
            rows={1}
            disabled={loading}
            className="flex-1 resize-none text-sm leading-6 outline-none placeholder:text-[var(--muted)]"
            style={{
              background: "transparent",
              color: "var(--foreground)",
              maxHeight: 120,
              scrollbarWidth: "none",
            }}
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200"
            style={{
              background: query.trim() && !loading ? "var(--accent-blue)" : "rgba(79,124,255,0.15)",
              color: query.trim() && !loading ? "#fff" : "var(--muted)",
              cursor: query.trim() && !loading ? "pointer" : "not-allowed",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
        <p className="text-center text-xs mt-2" style={{ color: "var(--muted)" }}>
          Using <strong>{MODES.find((m) => m.value === mode)?.desc}</strong>
          {strategy ? ` · ${STRATEGIES.find((s) => s.value === strategy)?.label}` : " · All strategies"}
          {" · "}Press Enter to send
        </p>
      </div>
    </div>
  );
}

// ── Empty state with suggestions ────────────────────────────────────────────
function EmptyState({ onSuggestionClick }: { onSuggestionClick: (q: string) => void }) {
  const suggestions = [
    "What projects are in Kadawatha?",
    "How much is SKYE BLOSSOM in KOTTAWA?",
    "What payment plans does PrimeLands offer?",
    "Tell me about GREEN EMBAZY HOMAGAMA facilities",
    "Compare apartments in Colombo and Negombo",
    "Which locations does PrimeLands have projects in?",
  ];

  return (
    <div className="fade-up flex flex-col items-center justify-center py-16 text-center">
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl mb-5"
        style={{ background: "linear-gradient(135deg, rgba(79,124,255,0.15), rgba(124,111,247,0.15))", border: "1px solid rgba(79,124,255,0.2)" }}
      >
        🏠
      </div>
      <h2 className="text-xl font-bold mb-2" style={{ color: "var(--foreground)" }}>
        PrimeLands Property Intelligence
      </h2>
      <p className="text-sm mb-8 max-w-md" style={{ color: "var(--muted)" }}>
        Ask any question about PrimeLands properties, pricing, locations, facilities, or payment plans. Select a chunking strategy and processing mode above.
      </p>
      <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestionClick(s)}
            className="text-left px-4 py-3 rounded-xl border text-xs transition-all duration-200 hover:scale-[1.02]"
            style={{
              background: "var(--card)",
              borderColor: "var(--border)",
              color: "var(--foreground)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--accent-blue)";
              e.currentTarget.style.background = "var(--card-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.background = "var(--card)";
            }}
          >
            <span style={{ color: "var(--accent-blue)", marginRight: 6 }}>→</span>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Message bubble ──────────────────────────────────────────────────────────
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`fade-up flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className="max-w-2xl rounded-2xl px-5 py-4"
        style={{
          background: isUser
            ? "linear-gradient(135deg, rgba(79,124,255,0.2), rgba(124,111,247,0.15))"
            : "var(--card)",
          border: `1px solid ${isUser ? "rgba(79,124,255,0.3)" : "var(--border)"}`,
        }}
      >
        {/* Content */}
        <div
          className="text-sm leading-7 whitespace-pre-wrap"
          style={{ color: "var(--foreground)" }}
        >
          {message.content}
        </div>

        {/* Meta info for AI messages */}
        {!isUser && message.meta && <MetaPanel meta={message.meta} />}
      </div>
    </div>
  );
}

// ── Meta panel (shown under AI responses) ───────────────────────────────────
function MetaPanel({ meta }: { meta: ChatResult }) {
  return (
    <div className="mt-4 pt-3 space-y-3" style={{ borderTop: "1px solid var(--border)" }}>
      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Mode badge */}
        <Badge
          color={meta.mode_used === "cag" ? "blue" : meta.mode_used === "crag" ? "amber" : "indigo"}
          label={meta.mode_used.toUpperCase()}
        />

        {/* Cache hit/miss badge */}
        {meta.cache_hit !== undefined && (
          <Badge
            color={meta.cache_hit ? "green" : "rose"}
            label={meta.cache_hit ? `⚡ Cache Hit (${meta.cache_source})` : "🔍 Cache Miss → RAG"}
          />
        )}

        {/* CRAG correction badge */}
        {meta.correction_applied !== undefined && (
          <Badge
            color={meta.correction_applied ? "amber" : "green"}
            label={meta.correction_applied ? "🔄 Correction Applied" : "✅ Confidence OK"}
          />
        )}

        {/* Strategy badge */}
        {meta.strategy_used && (
          <Badge color="cyan" label={`📦 ${meta.strategy_used}`} />
        )}

        {/* Generation time */}
        <Badge color="muted" label={`⏱ ${meta.generation_time.toFixed(2)}s`} />

        {/* Docs used */}
        {meta.docs_used !== undefined && (
          <Badge color="muted" label={`📄 ${meta.docs_used} docs`} />
        )}
      </div>

      {/* Confidence scores for CRAG */}
      {meta.confidence_initial !== undefined && (
        <div className="flex items-center gap-4 text-xs" style={{ color: "var(--muted)" }}>
          <span>
            Confidence: {(meta.confidence_initial * 100).toFixed(1)}%
            {meta.confidence_final !== undefined && meta.confidence_final !== meta.confidence_initial && (
              <span style={{ color: "var(--accent-green)" }}>
                {" → "}{(meta.confidence_final * 100).toFixed(1)}%
              </span>
            )}
          </span>
        </div>
      )}

      {/* Similarity score for CAG hits */} 
      {meta.similarity_score !== undefined && meta.similarity_score > 0 && (
        <div className="text-xs" style={{ color: "var(--muted)" }}>
          Similarity: {(meta.similarity_score * 100).toFixed(1)}%
          {meta.matched_query && meta.matched_query !== meta.answer && (
            <span> · Matched: &ldquo;{meta.matched_query.slice(0, 60)}...&rdquo;</span>
          )}
        </div>
      )}

      {meta.evidence_urls && meta.evidence_urls.length > 0 && (
        <div>
          <p className="text-xs font-semibold mb-1.5" style={{ color: "var(--muted)" }}>
            Sources:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {meta.evidence_urls.map((url, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs transition-colors"
                style={{
                  background: "rgba(245,158,11,0.1)",
                  border: "1px solid rgba(245,158,11,0.2)",
                  color: "#fbbf24",
                  textDecoration: "none",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(245,158,11,0.2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(245,158,11,0.1)";
                }}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
                {url.replace(/https?:\/\/(www\.)?/, "").slice(0, 40)}
                {url.length > 50 ? "..." : ""}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const BADGE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  blue:   { bg: "rgba(79,124,255,0.12)", border: "rgba(79,124,255,0.25)", text: "#7ea8ff" },
  indigo: { bg: "rgba(124,111,247,0.12)", border: "rgba(124,111,247,0.25)", text: "#a89bff" },
  green:  { bg: "rgba(16,209,122,0.12)", border: "rgba(16,209,122,0.25)", text: "#10d17a" },
  amber:  { bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.25)", text: "#fbbf24" },
  rose:   { bg: "rgba(244,63,94,0.12)", border: "rgba(244,63,94,0.25)", text: "#fb7185" },
  cyan:   { bg: "rgba(6,182,212,0.12)", border: "rgba(6,182,212,0.25)", text: "#22d3ee" },
  muted:  { bg: "rgba(255,255,255,0.04)", border: "rgba(255,255,255,0.08)", text: "var(--muted)" },
};

function Badge({ color, label }: { color: string; label: string }) {
  const c = BADGE_COLORS[color] || BADGE_COLORS.muted;
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}
    >
      {label}
    </span>
  );
}

function LoadingIndicator() {
  return (
    <div className="fade-up flex justify-start">
      <div
        className="rounded-2xl px-5 py-4 flex items-center gap-3 animate-pulse-border"
        style={{ background: "var(--card)", border: "1px solid var(--border)" }}
      >
        <div className="animate-spin-slow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2.5" strokeLinecap="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        </div>
        <span className="text-sm" style={{ color: "var(--muted)" }}>
          Processing query...
        </span>
      </div>
    </div>
  );
}
