"use client";

import { ArrowLeft, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { Button, Empty, ErrorNote, Initials, Pill, Skeleton } from "@/components/ui";
import { api, ApiError, useApi, useNow } from "@/lib/api";
import { ago, dateTime, FLAG, INTENT, POLICY_REASON, time } from "@/lib/format";
import type { Conversation, ConversationDetail, Decision } from "@/lib/types";

type View = "open" | "needs_human" | "resolved";
const VIEWS: { id: View; label: string; query: string }[] = [
  { id: "open", label: "Đang mở", query: "status=open" },
  { id: "needs_human", label: "Cần nhân viên", query: "needs_human=true&status=open" },
  { id: "resolved", label: "Đã xử lý", query: "status=resolved" },
];

export default function InboxPage() {
  return (
    <Suspense fallback={<Skeleton rows={6} />}>
      <Inbox />
    </Suspense>
  );
}

function Inbox() {
  const params = useSearchParams();
  const router = useRouter();
  const selected = params.get("c");
  const [view, setView] = useState<View>("open");
  const [q, setQ] = useState("");
  const query = VIEWS.find((v) => v.id === view)!.query + (q ? `&q=${encodeURIComponent(q)}` : "");
  const list = useApi<Conversation[]>(`/conversations?${query}`, 10000);
  const select = (id: string | null) => router.replace(id ? `/app/inbox?c=${id}` : "/app/inbox", { scroll: false });

  return (
    <div className="-m-4 flex h-[calc(100vh-48px)] sm:-m-6 lg:h-[calc(100vh-58px)]">
      <section
        aria-label="Danh sách hội thoại"
        className={`${selected ? "hidden md:flex" : "flex"} w-full flex-none flex-col border-r border-rule md:w-[340px]`}
      >
        <div className="px-4 pt-4">
          <h1 className="text-[22px] font-semibold">Hộp thư</h1>
          <div role="tablist" aria-label="Lọc hội thoại" className="mt-3 flex gap-4 border-b border-border">
            {VIEWS.map((v) => (
              <button
                key={v.id}
                role="tab"
                aria-selected={view === v.id}
                onClick={() => setView(v.id)}
                className={`-mb-px cursor-pointer border-b-2 pb-2 text-sm ${
                  view === v.id ? "border-accent font-semibold text-ink" : "border-transparent text-muted hover:text-ink"
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
          <label className="sr-only" htmlFor="inbox-search">
            Tìm khách
          </label>
          <input
            id="inbox-search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm theo tên khách"
            className="my-3 h-9 w-full rounded-[var(--radius-control)] border border-control px-3 text-sm focus:border-ink focus:outline-none"
          />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
          {list.loading && <div className="p-2"><Skeleton rows={6} /></div>}
          {list.error && <div className="p-2"><ErrorNote error={list.error} onRetry={list.reload} /></div>}
          {list.data?.length === 0 && (
            <Empty title="Không có hội thoại">
              {view === "open" ? "Tin nhắn Messenger mới sẽ xuất hiện ở đây." : "Thử bộ lọc khác."}
            </Empty>
          )}
          <ul>
            {list.data?.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => select(c.id)}
                  aria-current={selected === c.id ? "true" : undefined}
                  className={`flex w-full cursor-pointer items-start gap-3 rounded-lg px-2 py-3 text-left transition-colors duration-150 ${
                    selected === c.id ? "bg-active" : "hover:bg-raised"
                  }`}
                >
                  <Initials name={c.customer_name} />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className={`truncate ${c.ai_needs_human ? "font-semibold" : ""}`}>{c.customer_name}</span>
                      <span className="flex-none text-xs text-muted">{ago(c.last_message_at)}</span>
                    </span>
                    <span className="mt-0.5 flex items-center gap-2">
                      <span className="truncate text-sm text-muted">{c.last_message_preview || "—"}</span>
                      {c.ai_needs_human && <span className="size-1.5 flex-none rounded-full bg-accent" aria-label="Cần nhân viên" />}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {selected ? (
        <Thread key={selected} id={selected} onBack={() => select(null)} onChanged={list.reload} />
      ) : (
        <div className="hidden flex-1 place-items-center md:grid">
          <Empty title="Chọn một hội thoại">Gợi ý của AI và chính sách gửi tin hiển thị bên phải hội thoại.</Empty>
        </div>
      )}
    </div>
  );
}

function Thread({ id, onBack, onChanged }: { id: string; onBack: () => void; onChanged: () => void }) {
  const { data: c, error, reload, setData } = useApi<ConversationDetail>(`/conversations/${id}`, 8000);
  const [draft, setDraft] = useState("");
  const [fromSuggestion, setFromSuggestion] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<Decision | null>(null);
  const [actionError, setActionError] = useState<ApiError | null>(null);
  const [showAi, setShowAi] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const now = useNow();

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [c?.messages.length]);

  if (error) return <div className="flex-1 p-6"><ErrorNote error={error} onRetry={reload} /></div>;
  if (!c) return <div className="flex-1 p-6"><Skeleton rows={6} /></div>;

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    setActionError(null);
    try {
      await fn();
      await reload();
      onChanged();
    } catch (e) {
      setActionError(e as ApiError);
    } finally {
      setBusy(null);
    }
  }

  const send = () =>
    run("send", async () => {
      const r = await api<{ message: unknown; decision: Decision }>(`/conversations/${id}/messages`, {
        method: "POST",
        json: { text: draft, from_suggestion: fromSuggestion },
      });
      setNotice(r.decision.decision === "ALLOW" ? null : r.decision);
      if (r.message) {
        setDraft("");
        setFromSuggestion(false);
      }
    });

  const patch = (body: object) =>
    run("patch", async () => setData({ ...c, ...(await api<Conversation>(`/conversations/${id}`, { method: "PATCH", json: body })) }));

  const windowOpen = c.last_customer_message_at && now - new Date(c.last_customer_message_at).getTime() < 864e5;

  return (
    <div className="flex min-w-0 flex-1">
      <section aria-label={`Hội thoại với ${c.customer_name}`} className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-none items-center gap-3 border-b border-rule px-4 py-3">
          <button onClick={onBack} className="grid size-9 place-items-center rounded-lg md:hidden" aria-label="Quay lại danh sách">
            <ArrowLeft className="size-4" />
          </button>
          <Initials name={c.customer_name} />
          <div className="min-w-0 flex-1">
            <h2 className="truncate font-semibold">{c.customer_name}</h2>
            <p className="text-xs text-muted">
              Messenger · {windowOpen ? "trong cửa sổ 24 giờ" : "đã quá 24 giờ, không thể nhắn chủ động"}
            </p>
          </div>
          <Button variant="ghost" onClick={() => setShowAi(true)} className="xl:hidden" aria-label="Xem gợi ý AI">
            <Sparkles className="size-4 text-accent" strokeWidth={1.6} />
            <span className="hidden sm:inline">Gợi ý AI</span>
          </Button>
          {c.status !== "resolved" ? (
            <Button onClick={() => patch({ status: "resolved" })} busy={busy === "patch"}>Đánh dấu đã xử lý</Button>
          ) : (
            <Button onClick={() => patch({ status: "open" })} busy={busy === "patch"}>Mở lại</Button>
          )}
        </header>

        <ol className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
          {c.messages.map((m) => (
            <li key={m.id} className={`flex ${m.direction === "out" ? "justify-end" : ""}`}>
              <div className={`max-w-[75%] rounded-2xl px-3.5 py-2 ${m.direction === "out" ? "bg-ink text-white" : "bg-raised"}`}>
                <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                <p className={`mt-1 text-xs ${m.direction === "out" ? "text-white/70" : "text-muted"}`}>
                  {time(m.created_at)}
                  {m.direction === "out" && ` · ${{ human: "Nhân viên", ai: "AI", system: "Tin mẫu ngoài giờ", customer: "" }[m.actor]}`}
                  {m.provider_status === "dry_run" && " · chế độ thử (chưa gửi Meta)"}
                  {m.provider_status === "failed" && ` · gửi lỗi: ${m.error}`}
                </p>
              </div>
            </li>
          ))}
          <div ref={bottom} />
        </ol>

        <div className="flex-none border-t border-rule p-3">
          {notice && (
            <p role="alert" className="mb-2 rounded-md bg-[var(--pill-warning-bg)] px-3 py-2 text-sm text-[var(--pill-warning-ink)]">
              Chưa gửi: {notice.reasons.map((r) => POLICY_REASON[r] ?? r).join("; ")}
            </p>
          )}
          {actionError && <div className="mb-2"><ErrorNote error={actionError} /></div>}
          <label htmlFor="composer" className="sr-only">Soạn tin trả lời</label>
          <textarea
            id="composer"
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value);
              if (!e.target.value) setFromSuggestion(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && draft.trim()) send();
            }}
            rows={3}
            placeholder={`Trả lời ${c.customer_name}…`}
            className="w-full resize-none rounded-[var(--radius-control)] border border-control px-3 py-2 leading-relaxed focus:border-ink focus:outline-none"
          />
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-xs text-muted">Ctrl/⌘ + Enter để gửi</span>
            <Button variant="primary" onClick={send} busy={busy === "send"} disabled={!draft.trim()}>
              Gửi
            </Button>
          </div>
        </div>
      </section>

      <aside
        aria-label="Phân tích AI và khách hàng"
        className={`${showAi ? "fixed inset-0 z-40 block bg-surface" : "hidden"} overflow-y-auto p-4 xl:static xl:block xl:w-[320px] xl:flex-none xl:border-l xl:border-rule`}
      >
        <div className="mb-2 flex justify-end xl:hidden">
          <Button variant="ghost" onClick={() => setShowAi(false)} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </div>
        <AiPanel
          c={c}
          busy={busy}
          onUse={() => {
            setShowAi(false);
            setDraft(c.ai_suggested_reply ?? "");
            setFromSuggestion(true);
            document.getElementById("composer")?.focus();
          }}
          onAnalyze={() => run("analyze", () => api(`/conversations/${id}/analyze`, { method: "POST" }))}
          onTogglePause={() => patch({ automation_paused: !c.automation_paused })}
        />
      </aside>
    </div>
  );
}

function AiPanel({
  c,
  busy,
  onUse,
  onAnalyze,
  onTogglePause,
}: {
  c: ConversationDetail;
  busy: string | null;
  onUse: () => void;
  onAnalyze: () => void;
  onTogglePause: () => void;
}) {
  const now = useNow();
  const held = c.needs_ai_at && new Date(c.needs_ai_at).getTime() > now;
  return (
    <div className="space-y-6">
      <section>
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-1.5 font-semibold">
            <Sparkles className="size-4 text-accent" strokeWidth={1.6} aria-hidden /> Gợi ý của AI
          </h3>
          <Button variant="ghost" onClick={onAnalyze} busy={busy === "analyze"} className="h-8 px-2 text-xs">
            Phân tích lại
          </Button>
        </div>
        {held && <p className="mt-2 text-sm text-muted">Ngoài giờ trực: AI sẽ đọc toàn bộ tin lúc {dateTime(c.needs_ai_at!)}.</p>}
        {!c.ai_updated_at && !held && <p className="mt-2 text-sm text-muted">AI chưa phân tích hội thoại này.</p>}
        {c.ai_intent && (
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-muted">Nhu cầu</dt>
              <dd className="font-medium">{INTENT[c.ai_intent]}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-muted">Độ tin cậy</dt>
              <dd>{Math.round((c.ai_confidence ?? 0) * 100)}%</dd>
            </div>
          </dl>
        )}
        {c.ai_summary && <p className="mt-3 text-sm leading-relaxed">{c.ai_summary}</p>}
        {c.ai_flags.map((f) => (
          <p key={f} className="mt-3 rounded-md bg-[var(--pill-warning-bg)] px-3 py-2 text-sm text-[var(--pill-warning-ink)]">
            {FLAG[f] ?? f} — cần nhân viên kiểm tra trước khi gửi.
          </p>
        ))}
        {c.ai_suggested_reply && (
          <div className="mt-3 rounded-[var(--radius-card)] bg-[var(--pill-accent-bg)] p-3">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--pill-accent-ink)]">{c.ai_suggested_reply}</p>
            <Button onClick={onUse} className="mt-3 h-8 bg-surface text-xs">Dùng gợi ý này</Button>
          </div>
        )}
      </section>

      <section>
        <h3 className="font-semibold">Khách hàng</h3>
        <div className="mt-2 flex flex-col gap-2 text-sm">
          <Link href={`/app/customers?id=${c.customer_id}`} className="font-medium hover:underline">Xem hồ sơ khách</Link>
          <Link href={`/app/bookings?new=1&customer=${c.customer_id}&conversation=${c.id}`} className="font-medium hover:underline">
            Tạo lịch hẹn từ hội thoại
          </Link>
        </div>
        <label className="mt-4 flex cursor-pointer items-center justify-between gap-3 text-sm">
          <span>Tạm dừng tự động hoá cho khách này</span>
          <input type="checkbox" checked={c.automation_paused} onChange={onTogglePause} className="size-4 accent-[var(--accent)]" />
        </label>
      </section>

      <section>
        <h3 className="font-semibold">Quyết định gửi tin gần đây</h3>
        {c.decisions.length === 0 && <p className="mt-2 text-sm text-muted">Chưa có tin gửi đi.</p>}
        <ul className="mt-2 space-y-2">
          {c.decisions.slice(0, 5).map((d) => (
            <li key={d.id} className="flex items-start justify-between gap-2 text-sm">
              <span className="min-w-0">
                <span className="block">{d.reasons.map((r) => POLICY_REASON[r] ?? r).join("; ")}</span>
                <span className="text-xs text-muted">{dateTime(d.created_at)}</span>
              </span>
              <Pill tone={d.decision === "ALLOW" ? "positive" : d.decision === "HOLD" ? "warning" : "negative"}>
                {{ ALLOW: "Đã cho gửi", HOLD: "Tạm giữ", SKIP: "Chặn" }[d.decision]}
              </Pill>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
