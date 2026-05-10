import { useEffect, useState } from "react";
import { FileText, Plus, Trash2, RefreshCw, FileX } from "lucide-react";
import { api, type DocItem } from "@/lib/livedocs-api";

export function DocumentsTab({ workspace }: { workspace: string }) {
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [addName, setAddName] = useState("");
  const [addContent, setAddContent] = useState("");
  const [delName, setDelName] = useState("");

  async function load() {
    setLoading(true);
    try {
      const res = await api.listDocuments(workspace);
      setDocs(res.documents);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspace]);

  async function add() {
    if (!addName.trim() || !addContent.trim()) return;
    try {
      await api.addDocument({ filename: addName, content: addContent, workspace });
      setStatus(`Indexed ${addName}`);
      setAddName("");
      setAddContent("");
      load();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed");
    }
  }

  async function remove() {
    if (!delName.trim()) return;
    try {
      await api.deleteDocument(delName, workspace);
      setStatus(`Deleted ${delName}`);
      setDelName("");
      load();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-100">Knowledge Base</h2>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800/60 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Plus className="w-4 h-4 text-green-400" />
            <h3 className="text-sm font-semibold text-slate-100">Add Document</h3>
          </div>
          <input
            value={addName}
            onChange={(e) => setAddName(e.target.value)}
            placeholder="filename.txt"
            className="w-full mb-3 h-10 px-3 text-sm rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition"
          />
          <textarea
            value={addContent}
            onChange={(e) => setAddContent(e.target.value)}
            placeholder="Content..."
            className="w-full mb-3 px-3 py-2 text-sm rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition min-h-[80px] resize-y"
          />
          <button
            onClick={add}
            className="w-full h-10 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition shadow-lg shadow-brand-500/20"
          >
            Add &amp; Index
          </button>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Trash2 className="w-4 h-4 text-red-400" />
            <h3 className="text-sm font-semibold text-slate-100">Delete Document</h3>
          </div>
          <input
            value={delName}
            onChange={(e) => setDelName(e.target.value)}
            placeholder="filename.txt"
            className="w-full mb-3 h-10 px-3 text-sm rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition"
          />
          <button
            onClick={remove}
            className="w-full h-10 rounded-xl bg-red-500/90 hover:bg-red-500 text-white text-sm font-medium transition"
          >
            Delete
          </button>
        </div>
      </div>

      {status && (
        <div className="glass-card p-4 text-center text-sm text-slate-400">{status}</div>
      )}

      {docs.length === 0 ? (
        <div className="glass-card p-12 flex flex-col items-center text-slate-500">
          <FileX className="w-16 h-16 mb-3 opacity-30" />
          <p className="text-sm">No documents found.</p>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((d) => (
            <div
              key={d.filename}
              className="glass-card p-4 hover:border-brand-500/50 transition group"
            >
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-brand-400 shrink-0" />
                <span className="text-sm font-medium text-slate-100 truncate">{d.filename}</span>
              </div>
              <p className="text-xs text-slate-500">Size: {(d.size_bytes / 1024).toFixed(1)} KB</p>
              <p className="text-xs text-slate-500">Type: {d.doc_type}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
