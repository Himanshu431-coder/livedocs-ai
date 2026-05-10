import { useEffect, useRef, useState } from "react";
import { FileText, Layers, Database, Briefcase, RefreshCw, Pause, Play, X } from "lucide-react";
import { api, type Stats, type DocItem } from "@/lib/livedocs-api";

const PIPELINE = `Query → Orchestrator → Research → Analyze → Synthesize → Verify
                           │
                     RAG Engine
                 ┌──────┼──────┐
             ChromaDB        BM25
             (Dense)       (Sparse)
                 └──────┼──────┘
              RRF Fusion → LLM Reranker
                          │
              MCP Server (6 Tools)
                          │
              File Watcher (Real-Time)`;

const REFRESH_MS = 10_000;

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

export function AnalyticsTab({ workspace }: { workspace: string }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [live, setLive] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [selected, setSelected] = useState<DocItem | null>(null);
  const timerRef = useRef<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [s, d] = await Promise.all([
        api.stats(workspace),
        api.listDocuments(workspace).catch(() => ({ documents: [] as DocItem[], total: 0, workspace })),
      ]);
      setStats(s);
      setDocs(d.documents);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspace]);

  useEffect(() => {
    if (!live) {
      if (timerRef.current) window.clearInterval(timerRef.current);
      return;
    }
    timerRef.current = window.setInterval(load, REFRESH_MS);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [live, workspace]);

  const cards = [
    { icon: FileText, color: "blue-400", label: "Documents", value: stats?.total_documents ?? 0 },
    { icon: Layers, color: "purple-400", label: "Chunks", value: stats?.total_chunks ?? 0 },
    {
      icon: Database,
      color: "green-400",
      label: "BM25 Index",
      value: stats ? (stats.bm25_indexed ? "Active" : "Inactive") : "—",
    },
    { icon: Briefcase, color: "amber-400", label: "Workspace", value: workspace },
  ];

  const docMap = new Map(docs.map((d) => [d.filename, d] as const));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-2xl font-bold text-slate-100">Analytics</h2>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="text-[11px] text-slate-500">
              Updated {lastUpdated.toLocaleTimeString()}
              {live && <span className="ml-1 text-green-400">● live</span>}
            </span>
          )}
          <button
            onClick={() => setLive((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800/60 transition"
          >
            {live ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            {live ? "Pause" : "Resume"}
          </button>
          <button
            onClick={load}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800/60 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.label} className="glass-card p-5 flex flex-col items-center text-center">
              <Icon className="w-5 h-5 mb-2" style={{ color: `var(--color-${c.color})` }} />
              <div className="text-2xl font-bold text-slate-100">{c.value}</div>
              <div className="text-xs text-slate-500 mt-1">{c.label}</div>
            </div>
          );
        })}
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-slate-100 mb-3">
          Indexed Files {stats && <span className="text-slate-500 font-normal">· click for details</span>}
        </h3>
        {stats && stats.documents.length > 0 ? (
          <div className="space-y-1.5">
            {stats.documents.map((f) => {
              const meta = docMap.get(f);
              return (
                <button
                  key={f}
                  onClick={() => meta && setSelected(meta)}
                  disabled={!meta}
                  className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 transition text-left disabled:cursor-default disabled:hover:bg-slate-800/40"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                    <span className="text-sm text-slate-300 truncate">{f}</span>
                  </div>
                  {meta && (
                    <span className="text-[10px] text-slate-500 shrink-0">
                      {formatBytes(meta.size_bytes)} · {meta.doc_type}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No indexed files.</p>
        )}
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-brand-400 mb-3">Pipeline Architecture</h3>
        <pre className="bg-slate-950 rounded-xl p-4 text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800 leading-relaxed">
{PIPELINE}
        </pre>
      </div>

      {selected && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="glass-card-glow max-w-lg w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 mb-4">
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="w-5 h-5 text-brand-400 shrink-0" />
                <h4 className="text-base font-semibold text-slate-100 truncate">{selected.filename}</h4>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="p-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Type</dt>
                <dd className="text-slate-200 font-medium">{selected.doc_type}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Size</dt>
                <dd className="text-slate-200 font-medium">{formatBytes(selected.size_bytes)}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Modified</dt>
                <dd className="text-slate-200 font-medium">
                  {new Date(selected.modified_at).toLocaleString()}
                </dd>
              </div>
              <div className="col-span-2">
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Workspace</dt>
                <dd className="text-slate-200 font-medium">{workspace}</dd>
              </div>
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
