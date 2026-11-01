"use client";

import { ArrowUp, Sparkles } from "lucide-react";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { Button, ErrorNote } from "@/components/ui";
import { api, ApiError, useApi } from "@/lib/api";
import type { Artifact, ChatMessage } from "@/lib/types";

export type ChatScope = "script" | "media";

const SCOPE: Record<ChatScope, { title: string; about: string; kinds: Artifact["kind"][]; ideas: string[] }> = {
  script: {
    title: "Trợ lý kịch bản",
    about: "Nghiên cứu, viết, gộp và sửa kịch bản.",
    kinds: ["script"],
    ideas: ["Gộp kịch bản A và B thành một bản", "Viết 3 kịch bản nhấn ưu đãi lần đầu", "Rút câu mở đầu ngắn hơn"],
  },
  media: {
    title: "Trợ lý ảnh & video",
    about: "Góp ý và làm lại ảnh, video theo ý bạn.",
    kinds: ["image", "video", "short"],
    ideas: ["Làm lại ảnh với tông ấm, nhiều ánh sáng tự nhiên", "Đặt sản phẩm lên mặt khách, không đặt lên người", "Video này nên sửa gì?"],
  },
};

/** One assistant per scope, each with its own conversation. It never generates media itself:
 * a generation proposal comes back as a button the user must press (BRD §6.2). */
export function ProjectChat({
  projectId,
  scope,
  open,
  onChanged,
  onProposeGenerate,
}: {
  projectId: string;
  scope: ChatScope;
  open: Artifact | null;
  onChanged: () => void;
  onProposeGenerate: (scriptId: string, note?: string) => void;
}) {
  const history = useApi<ChatMessage[]>(`/projects/${projectId}/chat?scope=${scope}`);
  const [text, setText] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const meta = SCOPE[scope];
  const about = open && meta.kinds.includes(open.kind) ? open : null;

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [history.data?.length, pending]);

  async function send(message = text.trim()) {
    if (!message || pending) return;
    // Show the message at once; the reply takes a few seconds.
    setPending(message);
    setText("");
    setError(null);
    try {
      await api(`/projects/${projectId}/chat`, { method: "POST", json: { message, scope, artifact_id: about?.id ?? null } });
      await history.reload();
      onChanged();
    } catch (e) {
      setText(message);
      setError(e as ApiError);
    } finally {
      setPending(null);
    }
  }

  const msgs = history.data ?? [];
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex-none px-4 pb-2 pt-3">
        <p className="flex items-center gap-1.5 text-sm font-medium"><Sparkles className="size-4 text-accent" aria-hidden /> {meta.title}</p>
        <p className="mt-0.5 truncate text-xs text-faint">{about ? `Đang xem: ${about.display_name}` : meta.about}</p>
      </div>

      <ol className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-2" aria-live="polite">
        {history.data && !msgs.length && !pending && (
          <li className="space-y-2 pt-2">
            <p className="text-sm text-muted">Thử nhờ:</p>
            {meta.ideas.map((idea) => (
              <button key={idea} onClick={() => setText(idea)}
                className="block w-full cursor-pointer rounded-2xl bg-surface px-3 py-2 text-left text-sm transition-colors hover:bg-raised">
                {idea}
              </button>
            ))}
          </li>
        )}
        {msgs.map((m) => (
          <Bubble key={m.id} mine={m.role === "user"}>
            <p className="whitespace-pre-wrap">{m.content}</p>
            {m.action?.type === "propose_generation" && m.action.script_artifact_id && (
              <Button variant="primary" className="mt-2 h-8 text-xs" onClick={() => onProposeGenerate(m.action!.script_artifact_id!, m.action!.note)}>
                Xem lại và tạo
              </Button>
            )}
          </Bubble>
        ))}
        {pending && (
          <>
            <Bubble mine><p className="whitespace-pre-wrap">{pending}</p></Bubble>
            <Bubble>
              <span className="flex items-center gap-1 py-1" role="status" aria-label="AI đang trả lời">
                {[0, 150, 300].map((d) => <span key={d} className="size-1.5 animate-bounce rounded-full bg-muted" style={{ animationDelay: `${d}ms` }} />)}
              </span>
            </Bubble>
          </>
        )}
        <div ref={end} />
      </ol>

      <div className="flex-none p-3">
        {error && <div className="mb-2"><ErrorNote error={error} /></div>}
        <div className="flex items-end gap-2 rounded-[var(--radius-input)] border border-control bg-surface p-1.5 focus-within:border-ink">
          <label htmlFor={`chat-${scope}`} className="sr-only">Nhắn cho {meta.title.toLowerCase()}</label>
          <textarea id={`chat-${scope}`} value={text} onChange={(e) => setText(e.target.value)} rows={2}
            onKeyDown={(e) => {
              // Enter sends; Shift+Enter is a new line. Ignore Enter while a Vietnamese IME is composing.
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={about ? "Muốn đổi gì ở bản này?" : "Nhắn cho trợ lý…"}
            className="max-h-40 min-w-0 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm focus:outline-none" />
          <Button variant="primary" onClick={() => send()} disabled={!text.trim() || !!pending} aria-label="Gửi" className="size-9 flex-none rounded-full px-0">
            <ArrowUp className="size-4" aria-hidden />
          </Button>
        </div>
      </div>
    </div>
  );
}

function Bubble({ mine = false, children }: { mine?: boolean; children: ReactNode }) {
  return (
    <li className={`flex ${mine ? "justify-end" : ""}`}>
      <div className={`max-w-[88%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${mine ? "bg-ink text-ground" : "bg-surface"}`}>{children}</div>
    </li>
  );
}
