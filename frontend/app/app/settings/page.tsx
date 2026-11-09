"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent, type ReactNode } from "react";
import { StyleLibrary } from "@/components/style-library";
import { Button, Empty, ErrorNote, Field, PageTitle, Panel, Pill, Select, Skeleton } from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, ApiError, session, useApi } from "@/lib/api";
import { ROLE, vnd } from "@/lib/format";
import type { Branch, Brand, Knowledge, Member, Role, Service, SocialAccount } from "@/lib/types";

const TABS = [
  { id: "brand", label: "Thương hiệu" },
  { id: "services", label: "Sản phẩm, dịch vụ & giá" },
  { id: "faq", label: "Câu hỏi thường gặp" },
  { id: "branches", label: "Chi nhánh" },
  { id: "styles", label: "Phong cách hình ảnh" },
  { id: "integrations", label: "Facebook & Instagram" },
  { id: "ai", label: "Giờ trực AI" },
  { id: "members", label: "Thành viên" },
  { id: "delete", label: "Xoá cửa hàng" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export default function SettingsPage() {
  return (
    <Suspense fallback={<Skeleton rows={6} />}>
      <Settings />
    </Suspense>
  );
}

function Settings() {
  const params = useSearchParams();
  const router = useRouter();
  const { can } = useWorkspace();
  const tabs = TABS.filter((t) => t.id !== "delete" || can());
  const tab = (tabs.find((t) => t.id === params.get("tab"))?.id ?? "brand") as Tab;
  return (
    <>
      <PageTitle title="Cài đặt" sub="AI chỉ được dùng thông tin ở đây khi tư vấn khách; không có giá thì AI không báo giá." />
      <div role="tablist" aria-label="Mục cài đặt" className="mb-6 flex gap-5 overflow-x-auto border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => router.replace(`/app/settings?tab=${t.id}`, { scroll: false })}
            className={`-mb-px flex-none cursor-pointer border-b-2 pb-2 text-sm ${
              tab === t.id ? "border-accent font-semibold" : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "brand" && <BrandTab />}
      {tab === "services" && <ServicesTab />}
      {tab === "faq" && <KnowledgeTab />}
      {tab === "branches" && <BranchesTab />}
      {tab === "styles" && <StyleLibrary />}
      {tab === "integrations" && <IntegrationsTab connected={params.get("connected")} metaError={params.get("meta_error")} />}
      {tab === "ai" && <AiTab />}
      {tab === "members" && <MembersTab />}
      {tab === "delete" && <DeleteTab />}
    </>
  );
}

/** Submit helper: returns [busy, error, saved, run]. */
function useSubmit() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState(false);
  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      return true;
    } catch (e) {
      setError(e as ApiError);
      return false;
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, saved, run, fe: error?.fields ?? {} };
}

function SaveRow({ busy, saved, error, label = "Lưu" }: { busy: boolean; saved: boolean; error: ApiError | null; label?: string }) {
  return (
    <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
      <Button variant="primary" type="submit" busy={busy}>{label}</Button>
      <span role="status" className="text-sm text-positive">{saved ? "Đã lưu" : ""}</span>
      {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
    </div>
  );
}

const form = (e: FormEvent<HTMLFormElement>) => Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
const intOrNull = (v: string) => (v.trim() === "" ? null : Number(v.replace(/\D/g, "")));

function BrandTab() {
  const { can } = useWorkspace();
  const { data, error, reload } = useApi<Brand>("/brand");
  const s = useSubmit();
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Skeleton rows={6} />;
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const f = form(e);
        s.run(() => api("/brand", { method: "PUT", json: f }));
      }}
      className="grid max-w-3xl gap-4 sm:grid-cols-2"
      noValidate
    >
      <fieldset disabled={!can("admin", "marketing")} className="contents">
        <Field label="Tên cửa hàng" name="name" defaultValue={data.name} error={s.fe.name} />
        <Field
          label="Loại hình kinh doanh"
          name="industry"
          defaultValue={data.industry}
          placeholder="Spa, tiệm nail, quán cafe, shop thời trang…"
          hint="AI dùng để xưng hô khi tư vấn và viết quảng cáo đúng ngành"
          error={s.fe.industry}
        />
        <Field label="Hotline" name="hotline" defaultValue={data.hotline} inputMode="tel" />
        <Field label="Địa chỉ" name="address" defaultValue={data.address} />
        <Field label="Giờ mở cửa" name="opening_hours" defaultValue={data.opening_hours} placeholder="9:00 – 20:00, cả tuần" />
        <div className="sm:col-span-2">
          <Field label="Giới thiệu ngắn" name="description" textarea defaultValue={data.description} />
        </div>
        <Field label="Giọng điệu khi tư vấn" name="tone_of_voice" textarea defaultValue={data.tone_of_voice} hint="Ví dụ: gọi khách là chị/anh, xưng em, nhẹ nhàng" />
        <Field label="Không được nói" name="forbidden_claims" textarea defaultValue={data.forbidden_claims} hint="Ví dụ: không hứa trị dứt điểm mụn, không so sánh với cửa hàng khác" />
        <SaveRow {...s} />
      </fieldset>
    </form>
  );
}

function ServicesTab() {
  const list = useApi<Service[]>("/services");
  const [editing, setEditing] = useState<Service | "new" | null>(null);
  return (
    <ListTab
      title="Dịch vụ"
      empty="Chưa có dịch vụ. AI sẽ không báo giá cho đến khi bạn thêm."
      list={list}
      onNew={() => setEditing("new")}
      editor={editing && <ServiceForm item={editing === "new" ? null : editing} onDone={() => { setEditing(null); list.reload(); }} />}
      row={(s: Service) => (
        <>
          <div className="min-w-0 flex-1">
            <p className="font-medium">{s.name} {!s.active && <Pill>Đã tắt</Pill>}</p>
            <p className="truncate text-sm text-muted">{s.duration_minutes} phút{s.promotion ? ` · Ưu đãi: ${s.promotion}` : ""}</p>
          </div>
          <span className="text-right">
            {s.price_min == null ? <span className="text-muted">Chưa có giá</span> : s.price_max && s.price_max !== s.price_min ? `${vnd(s.price_min)} – ${vnd(s.price_max)}` : vnd(s.price_min)}
          </span>
          <Button variant="ghost" className="h-8 text-xs" onClick={() => setEditing(s)}>Sửa</Button>
        </>
      )}
    />
  );
}

function ServiceForm({ item, onDone }: { item: Service | null; onDone: () => void }) {
  const s = useSubmit();
  return (
    <Panel title={item ? `Sửa: ${item.name}` : "Dịch vụ mới"} className="mb-6">
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const f = form(e);
          const json = {
            name: f.name,
            description: f.description,
            duration_minutes: Number(f.duration_minutes || 60),
            price_min: intOrNull(f.price_min),
            price_max: intOrNull(f.price_max),
            promotion: f.promotion,
            active: f.active === "on",
          };
          if (await s.run(() => api(item ? `/services/${item.id}` : "/services", { method: item ? "PUT" : "POST", json }))) onDone();
        }}
        className="grid gap-4 sm:grid-cols-2"
        noValidate
      >
        <Field label="Tên dịch vụ" name="name" defaultValue={item?.name} error={s.fe.name} />
        <Field label="Thời lượng (phút)" name="duration_minutes" type="number" min={5} defaultValue={item?.duration_minutes ?? 60} error={s.fe.duration_minutes} />
        <Field label="Giá từ (VNĐ)" name="price_min" inputMode="numeric" defaultValue={item?.price_min ?? ""} error={s.fe.price_min} hint="Để trống nếu không công bố giá" />
        <Field label="Giá đến (VNĐ)" name="price_max" inputMode="numeric" defaultValue={item?.price_max ?? ""} error={s.fe.price_max} />
        <Field label="Mô tả" name="description" textarea defaultValue={item?.description} />
        <Field label="Ưu đãi đang áp dụng" name="promotion" textarea defaultValue={item?.promotion} hint="Ghi rõ điều kiện và thời hạn" />
        <label className="flex items-center gap-2 text-sm sm:col-span-2">
          <input type="checkbox" name="active" defaultChecked={item?.active ?? true} className="size-4 accent-[var(--accent)]" /> Đang cung cấp
        </label>
        <SaveRow {...s} />
      </form>
    </Panel>
  );
}

function KnowledgeTab() {
  const list = useApi<Knowledge[]>("/knowledge");
  const [editing, setEditing] = useState<Knowledge | "new" | null>(null);
  const s = useSubmit();
  const item = editing === "new" ? null : editing;
  return (
    <ListTab
      title="Câu hỏi thường gặp"
      empty="Thêm các câu khách hay hỏi: đỗ xe, thanh toán, chính sách huỷ lịch…"
      list={list}
      onNew={() => setEditing("new")}
      editor={
        editing && (
          <Panel title={item ? "Sửa mục" : "Mục mới"} className="mb-6">
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const f = form(e);
                if (await s.run(() => api(item ? `/knowledge/${item.id}` : "/knowledge", { method: item ? "PUT" : "POST", json: f }))) {
                  setEditing(null);
                  list.reload();
                }
              }}
              className="grid gap-4 sm:grid-cols-2"
              noValidate
            >
              <Field label="Câu hỏi / tiêu đề" name="title" defaultValue={item?.title} error={s.fe.title} />
              <Select label="Loại" name="kind" defaultValue={item?.kind ?? "faq"}>
                <option value="faq">Câu hỏi thường gặp</option>
                <option value="policy">Chính sách</option>
              </Select>
              <div className="sm:col-span-2">
                <Field label="Nội dung trả lời" name="content" textarea rows={4} defaultValue={item?.content} error={s.fe.content} />
              </div>
              <SaveRow {...s} />
            </form>
          </Panel>
        )
      }
      row={(k: Knowledge) => (
        <>
          <div className="min-w-0 flex-1">
            <p className="font-medium">{k.title}</p>
            <p className="truncate text-sm text-muted">{k.content}</p>
          </div>
          <Button variant="ghost" className="h-8 text-xs" onClick={() => setEditing(k)}>Sửa</Button>
          <Button variant="danger" className="h-8 text-xs" onClick={async () => { await api(`/knowledge/${k.id}`, { method: "DELETE" }); list.reload(); }}>Xoá</Button>
        </>
      )}
    />
  );
}

function BranchesTab() {
  const list = useApi<Branch[]>("/branches");
  const s = useSubmit();
  const [adding, setAdding] = useState(false);
  return (
    <ListTab
      title="Chi nhánh"
      empty="Thêm chi nhánh để đặt lịch hẹn."
      list={list}
      onNew={() => setAdding(true)}
      editor={
        adding && (
          <Panel title="Chi nhánh mới" className="mb-6">
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const f = form(e);
                if (await s.run(() => api("/branches", { method: "POST", json: { name: f.name, address: f.address, capacity: intOrNull(f.capacity) } }))) {
                  setAdding(false);
                  list.reload();
                }
              }}
              className="grid gap-4 sm:grid-cols-3"
              noValidate
            >
              <Field label="Tên" name="name" error={s.fe.name} />
              <Field label="Địa chỉ" name="address" />
              <Field label="Số khách cùng lúc" name="capacity" inputMode="numeric" hint="Để trống nếu không giới hạn" error={s.fe.capacity} />
              <SaveRow {...s} />
            </form>
          </Panel>
        )
      }
      row={(b: Branch) => (
        <>
          <div className="min-w-0 flex-1">
            <p className="font-medium">{b.name}</p>
            <p className="truncate text-sm text-muted">{b.address || "—"}</p>
          </div>
          <span className="text-right text-sm">{b.capacity ? `${b.capacity} khách cùng lúc` : "Không giới hạn"}</span>
        </>
      )}
    />
  );
}

function ListTab<T extends { id: string }>({
  title,
  empty,
  list,
  onNew,
  editor,
  row,
}: {
  title: string;
  empty: string;
  list: ReturnType<typeof useApi<T[]>>;
  onNew: () => void;
  editor: ReactNode;
  row: (item: T) => ReactNode;
}) {
  const { can } = useWorkspace();
  return (
    <div className="max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold">{title}{list.data ? ` · ${list.data.length}` : ""}</h2>
        {can("admin", "marketing") && <Button onClick={onNew}>Thêm</Button>}
      </div>
      {editor}
      {list.error && <ErrorNote error={list.error} onRetry={list.reload} />}
      {list.loading && <Skeleton rows={4} />}
      {list.data?.length === 0 && <Empty title={`Chưa có ${title.toLowerCase()}`}>{empty}</Empty>}
      <ul className="divide-y divide-rule">
        {list.data?.map((item) => (
          <li key={item.id} className="flex items-center gap-4 py-3">{row(item)}</li>
        ))}
      </ul>
    </div>
  );
}

function IntegrationsTab({ connected, metaError }: { connected: string | null; metaError: string | null }) {
  const { can } = useWorkspace();
  const list = useApi<SocialAccount[]>("/integrations/social-accounts");
  const [oauthError, setOauthError] = useState<ApiError | null>(null);
  const admin = can("admin");

  async function oauth() {
    try {
      const { url } = await api<{ url: string }>("/integrations/meta/connect", { method: "POST" });
      window.location.href = url;
    } catch (e) {
      setOauthError(e as ApiError);
    }
  }

  return (
    <div className="max-w-2xl">
      <Panel title="Tài khoản đã kết nối">
        {connected && <p role="status" className="mb-3 text-sm text-positive">Đã kết nối {connected} tài khoản.</p>}
        {metaError && <p role="alert" className="mb-3 text-sm text-negative">{metaError === "cancelled" ? "Bạn đã huỷ kết nối Facebook." : "Chưa kết nối được Facebook, vui lòng thử lại."}</p>}
        {list.loading && <Skeleton rows={2} />}
        {list.data?.length === 0 && <Empty title="Chưa kết nối Facebook Page">Kết nối để nhận tin nhắn Messenger vào hộp thư và đăng bài lên Facebook, Instagram.</Empty>}
        <ul className="divide-y divide-rule">
          {list.data?.map((a) => (
            <li key={a.id} className="flex items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="font-medium">{a.name || "Facebook Page"}</p>
                <p className="text-xs text-muted">{a.provider === "instagram" ? "Instagram · chỉ đăng bài" : "Facebook Page"}</p>
              </div>
              <Pill tone={a.status === "connected" ? "positive" : "neutral"}>{a.status === "connected" ? "Đang kết nối" : "Đã ngắt"}</Pill>
              {admin && a.status === "connected" && (
                <Button variant="danger" className="h-8 text-xs" onClick={async () => {
                  if (!confirm(a.provider === "instagram" ? `Ngắt kết nối ${a.name}? Không đăng bài lên tài khoản này được nữa.` : `Ngắt kết nối ${a.name}? Tin nhắn mới sẽ không vào hộp thư.`)) return;
                  await api(`/integrations/social-accounts/${a.id}`, { method: "DELETE" });
                  list.reload();
                }}>Ngắt</Button>
              )}
            </li>
          ))}
        </ul>
        {admin && (
          <div className="mt-4 space-y-2">
            <Button variant="primary" onClick={oauth}>Kết nối bằng Facebook</Button>
            <p className="text-xs text-muted">Instagram được kết nối cùng lúc nếu là tài khoản chuyên nghiệp đã liên kết với Page.</p>
            {oauthError && <ErrorNote error={oauthError} />}
          </div>
        )}
      </Panel>
    </div>
  );
}

function AiTab() {
  const { workspace, reload, can } = useWorkspace();
  const s = useSubmit();
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const f = form(e);
        const ok = await s.run(() =>
          api("/workspace", {
            method: "PATCH",
            json: {
              active_start: f.active_start,
              active_end: f.active_end,
              reply_mode: f.reply_mode,
              auto_reply_min_confidence: Number(f.auto_reply_min_confidence) / 100,
              quiet_hours_template: f.quiet_hours_template,
            },
          }),
        );
        if (ok) reload();
      }}
      className="grid max-w-3xl gap-4 sm:grid-cols-2"
      noValidate
    >
      <fieldset disabled={!can("admin")} className="contents">
        <Field label="AI bắt đầu trực" name="active_start" type="time" defaultValue={workspace.active_start} error={s.fe.active_start} />
        <Field label="AI nghỉ lúc" name="active_end" type="time" defaultValue={workspace.active_end} error={s.fe.active_end} hint="Ngoài giờ: không gọi AI, gửi 1 tin mẫu, gom tin trả lời đầu ca" />
        <Select label="Chế độ trả lời" name="reply_mode" defaultValue={workspace.reply_mode}>
          <option value="suggest">Chỉ gợi ý — nhân viên duyệt rồi gửi</option>
          <option value="auto">Tự trả lời khi AI chắc chắn</option>
        </Select>
        <Field
          label="Ngưỡng tự trả lời (%)"
          name="auto_reply_min_confidence"
          type="number"
          min={50}
          max={100}
          defaultValue={Math.round(workspace.auto_reply_min_confidence * 100)}
          error={s.fe.auto_reply_min_confidence}
          hint="Chỉ áp dụng ở chế độ tự trả lời; câu có giá chưa xác minh luôn chờ duyệt"
        />
        <div className="sm:col-span-2">
          <Field
            label="Tin mẫu ngoài giờ"
            name="quiet_hours_template"
            textarea
            defaultValue={workspace.quiet_hours_template}
            hint="Gõ {brand} để chèn tên cửa hàng, {active_start} để chèn giờ AI bắt đầu trực. Mỗi khách nhận tối đa 1 tin mỗi đêm."
            error={s.fe.quiet_hours_template}
          />
        </div>
        <SaveRow {...s} />
      </fieldset>
    </form>
  );
}

function MembersTab() {
  const { can, me } = useWorkspace();
  const list = useApi<Member[]>("/workspace/members");
  const s = useSubmit();
  const admin = can("admin");
  return (
    <div className="max-w-4xl">
      {admin && (
        <Panel title="Thêm thành viên" className="mb-6">
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const f = form(e);
              const target = e.currentTarget;
              if (await s.run(() => api("/workspace/members", { method: "POST", json: f }))) {
                target.reset();
                list.reload();
              }
            }}
            className="grid gap-4 sm:grid-cols-[1fr_220px_auto] sm:items-start"
            noValidate
          >
            <Field label="Email đã đăng ký" name="email" type="email" error={s.fe.email} hint="Người này cần tạo tài khoản trước" />
            <Select label="Vai trò" name="role" defaultValue="sales">
              {(Object.keys(ROLE) as Role[]).map((r) => <option key={r} value={r}>{ROLE[r]}</option>)}
            </Select>
            <div className="sm:pt-6"><Button variant="primary" type="submit" busy={s.busy}>Thêm</Button></div>
            {s.error && !Object.keys(s.fe).length && <div className="sm:col-span-3"><ErrorNote error={s.error} /></div>}
          </form>
        </Panel>
      )}
      {list.loading && <Skeleton rows={3} />}
      <ul className="divide-y divide-rule">
        {list.data?.map((m) => (
          <li key={m.user_id} className="flex items-center gap-4 py-3">
            <div className="min-w-0 flex-1">
              <p className="font-medium">{m.full_name || m.email}{m.user_id === me.id && " (bạn)"}</p>
              <p className="text-sm text-muted">{m.email}</p>
            </div>
            {admin && m.user_id !== me.id ? (
              <label className="sr-only" htmlFor={`role-${m.user_id}`}>Vai trò của {m.email}</label>
            ) : null}
            {admin && m.user_id !== me.id ? (
              <select
                id={`role-${m.user_id}`}
                value={m.role}
                onChange={async (e) => {
                  await api(`/workspace/members/${m.user_id}`, { method: "PATCH", json: { role: e.target.value } }).catch((err) => alert(err.message));
                  list.reload();
                }}
                className="h-9 rounded-[var(--radius-control)] border border-control px-2 text-sm"
              >
                {(Object.keys(ROLE) as Role[]).map((r) => <option key={r} value={r}>{ROLE[r]}</option>)}
              </select>
            ) : (
              <span className="text-sm">{ROLE[m.role]}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function DeleteTab() {
  const { me, workspace } = useWorkspace();
  const [typed, setTyped] = useState("");
  const s = useSubmit();
  const next = me.workspaces.find((w) => w.id !== workspace.id);
  return (
    <Panel title={`Xoá ${workspace.name}`} className="max-w-2xl">
      <p className="text-sm">
        Xoá vĩnh viễn cửa hàng này cùng toàn bộ dữ liệu của nó: khách hàng, hội thoại, lịch hẹn, dịch vụ và giá, dự án, ảnh,
        video và các Page đã kết nối. <b>Không khôi phục được.</b> Các cửa hàng khác của bạn không bị ảnh hưởng.
      </p>
      <form
        className="mt-5 flex flex-col gap-4"
        onSubmit={async (e) => {
          e.preventDefault();
          const ok = await s.run(() => api("/workspace", { method: "DELETE", json: { name: typed } }));
          if (!ok) return;
          if (next) session.setWorkspace(next.id);
          window.location.href = next ? "/app" : "/onboarding";
        }}
        noValidate
      >
        {s.error && <ErrorNote error={s.error} />}
        <Field
          label={`Gõ "${workspace.name}" để xác nhận`}
          name="confirm"
          autoComplete="off"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
        />
        <div>
          <Button variant="danger" type="submit" busy={s.busy} disabled={typed.trim() !== workspace.name.trim()}>
            Xoá vĩnh viễn
          </Button>
        </div>
      </form>
    </Panel>
  );
}
