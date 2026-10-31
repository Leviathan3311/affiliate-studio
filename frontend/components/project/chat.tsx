"use client";

import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button, ErrorNote } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import type { Artifact, ChatMessage } from "@/lib/types";

/** Project chat docked under the canvas. Talks about the open artifact; never generates media
 * itself — a generation proposal comes back as a button the user must press (BRD §6.2). */
export function ProjectChat({
  projectId,
  open,
  onChanged,
  onProposeGenerate,
}: {
  projectId: string;
  open: Artifact | null;
  onChanged: () => void;
  onProposeGenerate: (scriptId: string) => void;
}) {
  const history = useApi<ChatMessage[]>(`/projects/${projectId}/chat`);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [expanded, setExpanded] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [history.data?.length, expanded]);

  async function send() {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${projectId}/chat`, {
        method: "POST",
        json: { message: text.trim(), artifact_id: open?.kind === "script" ? open.id : null },
      });
      setText("");
      setExpanded(true);
      await history.reload();
      onChanged();
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  const msgs = history.data ?? [];
  const context = open?.kind === "script" ? open.display_name : null;
  return (
    <div className="flex-none border-t border-rule bg-surface">
      {expanded && (
        <ol className="max-h-72 space-y-3 overflow-y-auto px-4 pt-3" aria-live="polite">
          {msgs.length === 0 && <li className="text-sm text-muted">Hỏi AI về project, yêu cầu nghiên cứu, viết hoặc sửa kịch bản.</li>}
          {msgs.map((m) => (
            <li key={m.id} className={`flex ${m.role === "user" ? "justify-end" : ""}`}>
              <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${m.role === "user" ? "bg-ink text-white" : "bg-raised"}`}>
                <p className="whitespace-pre-wrap">{m.content}</p>
                {m.action?.type === "propose_generation" && m.action.script_artifact_id && (
                  <Button className="mt-2 h-8 bg-surface text-xs" onClick={() => onProposeGenerate(m.action!.script_artifact_id!)}>
                    Xem lại và tạo ảnh & video
                  </Button>
                )}
              </div>
            </li>
          ))}
          <div ref={end} />
        </ol>
      )}
      <div className="p-3">
        {error && <div className="mb-2"><ErrorNote error={error} /></div>}
        <div className="mb-1.5 flex items-center justify-between text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <Sparkles className="size-3.5 text-accent" aria-hidden />
            {context ? `Đang trao đổi về: ${context}` : "Trợ lý project (Gemini)"}
          </span>
          <button onClick={() => setExpanded((v) => !v)} className="flex cursor-pointer items-center gap-1 hover:text-ink" aria-expanded={expanded}>
            {expanded ? <ChevronDown className="size-3.5" /> : <ChevronUp className="size-3.5" />}
            {msgs.length} tin nhắn
          </button>
        </div>
        <div className="flex gap-2">
          <label htmlFor="project-chat" className="sr-only">Nhắn cho trợ lý project</label>
          <textarea id="project-chat" value={text} onChange={(e) => setText(e.target.value)} rows={2}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send(); }}
            placeholder={context ? "Ví dụ: rút hook ngắn hơn, nhấn mạnh ưu đãi lần đầu" : "Ví dụ: nghiên cứu đối thủ rồi viết 3 kịch bản"}
            className="min-w-0 flex-1 resize-none rounded-[var(--radius-control)] border border-control px-3 py-2 text-sm focus:border-ink focus:outline-none" />
          <Button variant="primary" onClick={send} busy={busy} disabled={!text.trim()} className="self-end">Gửi</Button>
        </div>
      </div>
    </div>
  );
}
