import { useEffect, useState } from "react";
import { Plug } from "lucide-react";
import { api, type MCPManifest } from "@/lib/livedocs-api";

const CLAUDE_CONFIG = `{
  "mcpServers": {
    "livedocs": {
      "url": "http://localhost:8000/mcp"
    }
  }
}`;

const REST_EXAMPLE = `curl http://localhost:8000/api/v1/mcp/manifest

curl -X POST http://localhost:8000/api/v1/mcp/call \\
  -H "Content-Type: application/json" \\
  -d '{"tool_name":"search_documents","arguments":{"query":"secret code"}}'`;

export function McpToolsTab() {
  const [manifest, setManifest] = useState<MCPManifest | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.mcpManifest().then(setManifest).catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Model Context Protocol</h2>
        <p className="text-sm text-slate-500 mt-1">
          MCP allows AI models (Claude, Cursor, etc.) to discover and call LiveDocs tools.
        </p>
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-brand-400 mb-3">Connect Claude Desktop</h3>
        <pre className="bg-slate-950 rounded-xl p-4 text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800">
{CLAUDE_CONFIG}
        </pre>
        <p className="text-xs text-slate-500 mt-2">Add to claude_desktop_config.json</p>
      </div>

      {error && <div className="glass-card p-4 text-sm text-red-400">{error}</div>}

      <div className="grid gap-4 md:grid-cols-2">
        {manifest?.tools.map((tool) => (
          <div key={tool.name} className="glass-card p-4 hover:border-brand-500/50 transition">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center">
                <Plug className="w-4 h-4 text-brand-400" />
              </div>
              <code className="text-sm font-bold text-brand-300">{tool.name}</code>
            </div>
            <p className="text-xs text-slate-400 mb-3">{tool.description}</p>
            <div className="space-y-1">
              {Object.entries(tool.inputSchema.properties).map(([pname, p]) => (
                <div key={pname} className="flex items-center gap-2 text-[11px]">
                  <code className="text-purple-300 font-mono">{pname}</code>
                  <span className="text-slate-600">{p.type}</span>
                  {tool.inputSchema.required?.includes(pname) && (
                    <span className="text-[9px] uppercase tracking-wide text-amber-400 px-1.5 py-0.5 rounded bg-amber-400/10">
                      required
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-green-400 mb-3">REST API</h3>
        <pre className="bg-slate-950 rounded-xl p-4 text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800">
{REST_EXAMPLE}
        </pre>
      </div>
    </div>
  );
}
