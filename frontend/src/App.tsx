import { useEffect, useState } from "react";
import { Zap, MessageSquare, FileText, Plug, BarChart3 } from "lucide-react";
import { AgenticQueryTab } from "./AgenticQueryTab";
import { DocumentsTab } from "./DocumentsTab";
import { McpToolsTab } from "./McpToolsTab";
import { AnalyticsTab } from "./AnalyticsTab";

type TabId = "query" | "docs" | "mcp" | "analytics";

const TABS: { id: TabId; label: string; icon: typeof MessageSquare }[] = [
  { id: "query", label: "Agentic Query", icon: MessageSquare },
  { id: "docs", label: "Documents", icon: FileText },
  { id: "mcp", label: "MCP Tools", icon: Plug },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
];

const WS_KEY = "livedocs:workspace";
const TAB_KEY = "livedocs:tab";
const VALID_TABS: TabId[] = ["query", "docs", "mcp", "analytics"];

function readInitial() {
  if (typeof window === "undefined") return { ws: "default", tab: "query" as TabId };
  const url = new URL(window.location.href);
  const urlWs = url.searchParams.get("ws");
  const urlTab = url.searchParams.get("tab") as TabId | null;
  let ws = urlWs ?? "default";
  let tab: TabId = urlTab && VALID_TABS.includes(urlTab) ? urlTab : "query";
  try {
    if (!urlWs) ws = localStorage.getItem(WS_KEY) ?? "default";
    if (!urlTab) {
      const stored = localStorage.getItem(TAB_KEY) as TabId | null;
      if (stored && VALID_TABS.includes(stored)) tab = stored;
    }
  } catch {
    /* noop */
  }
  return { ws, tab };
}

export function LiveDocsApp() {
  const initial = typeof window !== "undefined" ? readInitial() : { ws: "default", tab: "query" as TabId };
  const [tab, setTab] = useState<TabId>(initial.tab);
  const [workspace, setWorkspace] = useState(initial.ws);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  // Persist to localStorage + URL search params (without page reload)
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(WS_KEY, workspace);
      localStorage.setItem(TAB_KEY, tab);
    } catch {
      /* noop */
    }
    const url = new URL(window.location.href);
    url.searchParams.set("ws", workspace);
    url.searchParams.set("tab", tab);
    window.history.replaceState({}, "", url.toString());
  }, [workspace, tab]);

  // Listen to back/forward navigation
  useEffect(() => {
    function onPop() {
      const { ws, tab } = readInitial();
      setWorkspace(ws);
      setTab(tab);
    }
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-30 backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/30">
              <Zap className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-slate-100 leading-tight">
                LiveDocs AI
              </h1>
              <p className="text-[11px] text-slate-500 leading-tight">
                Agentic Knowledge Intelligence
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <input
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value || "default")}
              className="h-8 px-3 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition w-32"
              placeholder="workspace"
            />
            <span className="text-[10px] font-medium px-2 py-1 rounded-md bg-brand-600/20 text-brand-300 border border-brand-500/30">
              v2.0
            </span>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 flex gap-1">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-200 ${
                  active
                    ? "text-brand-400 border-brand-500"
                    : "text-slate-500 border-transparent hover:text-slate-300"
                }`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
        {tab === "query" && (
          <AgenticQueryTab
            workspace={workspace}
            conversationId={conversationId}
            setConversationId={setConversationId}
          />
        )}
        {tab === "docs" && <DocumentsTab workspace={workspace} />}
        {tab === "mcp" && <McpToolsTab />}
        {tab === "analytics" && <AnalyticsTab workspace={workspace} />}
      </main>

      <footer className="border-t border-slate-800/60 py-4 text-center text-xs text-slate-600">
        Built by Himanshu Tapde | AI/ML Engineer | LiveDocs AI v2
      </footer>
    </div>
  );
}
