import { useEffect, useRef, useState, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send, Loader2, Sparkles, ChevronDown, ChevronRight, FileText, FileCode,
  Layers, Activity, Clock, Bot, Compass, Search, BarChart2, Wand2, ShieldCheck,
  User, Plus, X,
} from "lucide-react";
import { api, type QueryResponse, type AgentStep } from "@/lib/livedocs-api";

const EXAMPLES = [
  "What is the secret code?",
  "Who is the CEO and what is their background?",
  "Compare remote work policy with benefits",
  "Analyze the product roadmap for risks",
  "What are the project milestones?",
  "What is the total budget across projects?",
];

const AGENT_STYLES: Record<AgentStep["agent"], { color: string; icon: typeof Bot }> = {
  orchestrator: { color: "amber-400", icon: Compass },
  researcher: { color: "blue-400", icon: Search },
  analyst: { color: "purple-400", icon: BarChart2 },
  synthesizer: { color: "green-400", icon: Wand2 },
  verifier: { color: "emerald-400", icon: ShieldCheck },
};

interface ChatTurn {
  id: string;
  question: string;
  response: QueryResponse;
}

interface PersistedSession {
  conversationId?: string;
  turns: ChatTurn[];
}

const sessionKey = (ws: string) => `livedocs:session:${ws}`;

function loadSession(ws: string): PersistedSession {
  if (typeof window === "undefined") return { turns: [] };
  try {
    const raw = localStorage.getItem(sessionKey(ws));
    if (!raw) return { turns: [] };
    return JSON.parse(raw) as PersistedSession;
  } catch {
    return { turns: [] };
  }
}

interface Props {
  workspace: string;
  conversationId?: string;
  setConversationId: (id: string | undefined) => void;
}

export function AgenticQueryTab({ workspace, conversationId, setConversationId }: Props) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Hydrate from localStorage on workspace change
  useEffect(() => {
    const s = loadSession(workspace);
    setTurns(s.turns);
    setConversationId(s.conversationId);
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspace]);

  // Persist
  useEffect(() => {
    if (typeof window === "undefined") return;
    const data: PersistedSession = { conversationId, turns };
    localStorage.setItem(sessionKey(workspace), JSON.stringify(data));
  }, [workspace, conversationId, turns]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, loading]);

  async function submit(question: string) {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError(null);
    setInput("");
    try {
      const res = await api.query({ question, workspace, conversation_id: conversationId });
      setConversationId(res.conversation_id);
      setTurns((t) => [...t, { id: `${Date.now()}`, question, response: res }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit(input);
  }

  function newSession() {
    setTurns([]);
    setConversationId(undefined);
    setError(null);
    if (typeof window !== "undefined") localStorage.removeItem(sessionKey(workspace));
  }

  const isEmpty = turns.length === 0 && !loading;
  const q = search.trim().toLowerCase();
  const filteredTurns = q
    ? turns.filter(
        (t) =>
          t.question.toLowerCase().includes(q) ||
          t.response.answer.toLowerCase().includes(q) ||
          t.response.citations.some((c) => c.source_file.toLowerCase().includes(q)),
      )
    : turns;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="text-xs text-slate-500">
          {conversationId ? (
            <>Session <span className="text-brand-400 font-mono">{conversationId.slice(0, 8)}</span> · {turns.length} turn{turns.length === 1 ? "" : "s"}</>
          ) : (
            <>New session</>
          )}
        </div>
        <div className="flex items-center gap-2">
          {turns.length > 0 && (
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search chat..."
                className="h-8 pl-8 pr-7 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 w-48"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 p-0.5 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          )}
          {turns.length > 0 && (
            <button
              onClick={newSession}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800/60 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              New session
            </button>
          )}
        </div>
      </div>

      {q && (
        <div className="text-xs text-slate-500">
          Showing {filteredTurns.length} of {turns.length} turn{turns.length === 1 ? "" : "s"}
        </div>
      )}

      {filteredTurns.map((t) => (
        <ChatTurnView key={t.id} turn={t} highlight={q} />
      ))}

      {loading && (
        <div className="glass-card p-4 flex items-center gap-3 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
          Agents working on it...
        </div>
      )}

      {error && (
        <div className="glass-card p-4 text-sm text-red-400 border-red-500/40">{error}</div>
      )}

      <div ref={bottomRef} />

      <form onSubmit={onSubmit} className="glass-card-glow p-4 sticky bottom-4">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your documents..."
            disabled={loading}
            className="flex-1 h-11 px-4 text-sm rounded-xl bg-slate-900 border border-slate-700 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="h-11 px-5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium flex items-center gap-2 transition shadow-lg shadow-brand-500/20 hover:shadow-brand-500/40 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Thinking...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Ask
              </>
            )}
          </button>
        </div>
        {isEmpty && (
          <div className="mt-4 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => submit(ex)}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-400 hover:text-brand-300 hover:border-brand-500/50 transition"
              >
                {ex}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}

function ChatTurnView({ turn }: { turn: ChatTurn; highlight?: string }) {
  const { question, response } = turn;
  const [citationsOpen, setCitationsOpen] = useState(false);
  const [pipelineOpen, setPipelineOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-slate-800/60 border border-slate-700/40 flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-slate-300" />
        </div>
        <div className="flex-1 pt-1.5 text-sm text-slate-100">{question}</div>
      </div>

      <MetricsBar response={response} />

      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <span className="text-sm font-semibold text-brand-400">Answer</span>
        </div>
        <div className="prose-livedocs">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{response.answer}</ReactMarkdown>
        </div>
      </div>

      <div className="glass-card p-4">
        <button
          onClick={() => setCitationsOpen((v) => !v)}
          className="w-full flex items-center justify-between text-sm font-semibold text-blue-400"
        >
          <span>Citations ({response.citations.length})</span>
          {citationsOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        {citationsOpen && (
          <div className="mt-3 space-y-2">
            {response.citations.map((c, i) => (
              <div key={i} className="rounded-xl bg-slate-800/50 border border-slate-700/40 p-3">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 text-blue-300 text-xs font-medium min-w-0">
                    <FileText className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{c.source_file}</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 shrink-0">
                    Score: {c.relevance_score.toFixed(4)}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{c.chunk_text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="glass-card p-4">
        <button
          onClick={() => setPipelineOpen((v) => !v)}
          className="w-full flex items-center justify-between text-sm font-semibold text-purple-400"
        >
          <span>Agent Pipeline ({response.agent_trace.length} steps)</span>
          {pipelineOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        {pipelineOpen && (
          <div className="mt-3 space-y-2">
            {response.agent_trace.map((step, i) => {
              const style = AGENT_STYLES[step.agent] ?? AGENT_STYLES.orchestrator;
              const Icon = style.icon;
              return (
                <div
                  key={i}
                  className="rounded-xl border-l-4 p-3 bg-slate-800/40"
                  style={{
                    borderLeftColor: `var(--color-${style.color})`,
                    borderTop: "1px solid color-mix(in oklab, var(--color-slate-700) 40%, transparent)",
                    borderRight: "1px solid color-mix(in oklab, var(--color-slate-700) 40%, transparent)",
                    borderBottom: "1px solid color-mix(in oklab, var(--color-slate-700) 40%, transparent)",
                  }}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-xs">
                      <Icon className="w-3.5 h-3.5" style={{ color: `var(--color-${style.color})` }} />
                      <span className="font-bold uppercase tracking-wide" style={{ color: `var(--color-${style.color})` }}>
                        {step.agent}
                      </span>
                      <span className="text-slate-500">→ {step.action}</span>
                    </div>
                    <span className="text-[10px] text-slate-400/60">{step.latency_ms}ms</span>
                  </div>
                  <p className="text-[11px] text-slate-300/70">Thought: {step.thought}</p>
                  <p className="text-[11px] text-slate-300/80">Result: {step.result}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricsBar({ response }: { response: QueryResponse }) {
  const items = [
    { icon: Layers, label: "Complexity", value: response.complexity },
    { icon: Activity, label: "Confidence", value: `${Math.round(response.confidence_score * 100)}%` },
    { icon: Clock, label: "Latency", value: `${response.total_latency_ms}ms` },
    { icon: FileText, label: "Docs", value: response.documents_searched },
    { icon: FileCode, label: "Chunks", value: response.chunks_retrieved },
    { icon: Bot, label: "Model", value: response.model_used },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((it) => {
        const Icon = it.icon;
        return (
          <div
            key={it.label}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/40"
          >
            <Icon className="w-3 h-3 text-slate-400" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">{it.label}</span>
            <span className="text-xs font-bold text-slate-300 truncate max-w-[200px]">{String(it.value)}</span>
          </div>
        );
      })}
    </div>
  );
}
