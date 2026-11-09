"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { LegalLinks } from "./legal";
import { Mark } from "./shell";

// Sample shops for the live demo. Prices are examples a shop would type into its own price list.
const SHOPS = [
  {
    id: "cafe",
    label: "Quán cafe",
    name: "Cà Phê Mộc",
    photo: "/landing/cafe.jpg",
    alt: "Một quán cafe trong phố cổ Hà Nội",
    ask: "Cà phê muối bao nhiêu vậy shop? Có giao qua Bình Thạnh không ạ?",
    reply:
      "Dạ cà phê muối bên em 35.000đ một ly ạ. Bên em giao qua Bình Thạnh bằng GrabFood, phí ship theo app. Anh/chị muốn đặt mấy ly để em lên đơn ạ?",
    price: "Cà phê muối · 35.000đ",
    intent: "Hỏi giá",
    score: 72,
  },
  {
    id: "clothes",
    label: "Shop quần áo",
    name: "Lá Store",
    photo: "/landing/clothes.jpg",
    alt: "Một cửa hàng quần áo bày ra vỉa hè ở phố cổ Hà Nội",
    ask: "Sơ mi linen trắng còn size M không shop? Giá sao ạ?",
    reply:
      "Dạ sơ mi linen trắng 389.000đ ạ. Size M em kiểm tra kho rồi báo chị trong ít phút nha. Chị cho em xin chiều cao, cân nặng để tư vấn size chuẩn hơn ạ.",
    price: "Sơ mi linen · 389.000đ",
    intent: "Hỏi giá",
    score: 64,
  },
  {
    id: "flowers",
    label: "Tiệm hoa",
    name: "Hoa Nhà Cúc",
    photo: "/landing/flowers.jpg",
    alt: "Một tiệm hoa trên đường Nguyễn Hữu Cảnh, quận 1",
    ask: "Bó hướng dương 10 bông giao trưa mai ở quận 3 được không em?",
    reply:
      "Dạ được ạ. Bó 10 bông hướng dương bên em 450.000đ, giao nội thành quận 3 miễn phí. Anh/chị cho em xin giờ nhận và lời nhắn trên thiệp nha.",
    price: "Hướng dương 10 bông · 450.000đ",
    intent: "Đặt hàng",
    score: 91,
  },
  {
    id: "lanterns",
    label: "Đồ lưu niệm",
    name: "Đèn Lồng Phố Hội",
    photo: "/landing/lanterns.jpg",
    alt: "Một tiệm đèn lồng ở Hội An buổi tối",
    ask: "Đèn lồng lụa cỡ 40cm giá sao? Gửi ra Hà Nội mất mấy ngày ạ?",
    reply:
      "Dạ đèn lồng lụa 40cm bên em 180.000đ một chiếc ạ. Gửi ra Hà Nội khoảng 3 đến 4 ngày. Anh/chị lấy mấy chiếc và màu gì để em báo tổng tiền ạ?",
    price: "Đèn lồng lụa 40cm · 180.000đ",
    intent: "Hỏi giá",
    score: 68,
  },
  {
    id: "spa",
    label: "Spa",
    name: "Lotus Spa",
    photo: null,
    alt: "",
    ask: "Gội đầu dưỡng sinh giá sao em? Chị đang có thai làm được không?",
    reply:
      "Dạ gội đầu dưỡng sinh bên em 150.000đ cho 60 phút ạ. Vì chị đang mang thai, em xin phép để chuyên viên gọi tư vấn trực tiếp cho chị nha.",
    price: "Gội đầu dưỡng sinh · 150.000đ",
    intent: "Hỏi giá",
    score: 70,
    human: true,
  },
] as const;

type Shop = (typeof SHOPS)[number];

function Messenger({ shop, night }: { shop: Shop; night: boolean }) {
  const time = night ? "23:47" : "14:20";
  const reply = night
    ? `Cảm ơn anh/chị đã nhắn tin cho ${shop.name}! Nhân viên đã nghỉ ca tối, 8:00 sáng mai bên em gửi giá và tư vấn chi tiết cho anh/chị nhé ạ!`
    : shop.reply;
  return (
    <div data-ui className="w-full max-w-[420px] rounded-xl bg-surface text-[14px] shadow-2xl shadow-black/50">
      <div className="flex items-center gap-2.5 border-b border-border px-[20px] py-3">
        <span className="grid size-8 place-items-center rounded-full bg-raised text-[13px] font-semibold">
          {shop.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
        </span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate font-semibold">{shop.name}</p>
          <p className="text-[13px] text-muted">Messenger · {night ? "ngoài giờ trực" : "AI đang trực"}</p>
        </div>
        <span className="rounded-full bg-[var(--pill-positive-bg)] px-2 py-0.5 text-[13px] text-[var(--pill-positive-ink)]">
          {night ? "Tin chờ sáng" : "Tự trả lời"}
        </span>
      </div>
      <div className="flex flex-col gap-3 px-[20px] py-4">
        <p className="self-center text-[13px] text-muted">Hôm nay {time}</p>
        <p className="max-w-[85%] self-start rounded-2xl rounded-bl-md bg-raised px-3.5 py-2.5">{shop.ask}</p>
        <div key={`${shop.id}-${night}`} className="landing-pop max-w-[85%] self-end">
          <p className="rounded-2xl rounded-br-md bg-[#2f6fe4] px-3.5 py-2.5 text-white">{reply}</p>
          <p className="mt-1 text-right text-[13px] text-muted">{night ? "Tin tự động, 1 lần mỗi đêm" : "AI · đã gửi"}</p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-px border-t border-border bg-border text-[13px]">
        <div className="bg-surface px-3 py-2.5">
          <p className="text-muted">Nhu cầu</p>
          <p className="font-medium">{night ? "Chờ phân tích" : shop.intent}</p>
        </div>
        <div className="bg-surface px-3 py-2.5">
          <p className="text-muted">Điểm khách</p>
          <p className="font-medium tabular-nums">{night ? "–" : `${shop.score}/100`}</p>
        </div>
        <div className="bg-surface px-3 py-2.5">
          <p className="text-muted">Giá dùng</p>
          <p className="truncate font-medium" title={shop.price}>
            {night ? "Không báo giá" : shop.price.split(" · ")[1]}
          </p>
        </div>
      </div>
      {!night && "human" in shop && (
        <p className="border-t border-border px-[20px] py-2.5 text-[13px] text-[var(--pill-warning-ink)]">
          Khách có thai: đã báo nhân viên vào xem
        </p>
      )}
    </div>
  );
}

function Hero() {
  const [shopId, setShopId] = useState<Shop["id"]>("cafe");
  const [night, setNight] = useState(false);
  const shop = SHOPS.find((s) => s.id === shopId)!;
  return (
    <section className="mx-auto grid max-w-[1240px] gap-10 px-[20px] pb-20 pt-10 sm:px-8 lg:grid-cols-[6fr_6fr] lg:items-center lg:pt-16">
      <div>
        <h1 className="text-[clamp(32px,3.7vw,52px)] font-semibold leading-[1.08] tracking-tight">
          <span className="block whitespace-nowrap">Khách hỏi giá,</span>
          <span className="block whitespace-nowrap">AI trả lời đúng giá.</span>
        </h1>
        <p className="mt-6 max-w-[34ch] text-[18px]">
          GrowthPilot trả lời tin nhắn Facebook bằng bảng giá của chính cửa hàng bạn, giữ danh sách khách, lịch hẹn và
          tự làm video quảng cáo cho Facebook, Instagram.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link
            href="/register"
            className="inline-flex h-12 items-center rounded-[var(--radius-control)] bg-ink px-6 text-[16px] font-medium text-ground hover:bg-ink/85"
          >
            Dùng thử 14 ngày miễn phí
          </Link>
          <span className="text-[14px] text-muted">Không cần thẻ, không cần biết kỹ thuật</span>
        </div>
      </div>
      <div>
        <div role="group" aria-label="Chọn loại cửa hàng" className="mb-3 flex flex-wrap gap-2">
          {SHOPS.map((s) => (
            <button
              key={s.id}
              onClick={() => setShopId(s.id)}
              aria-pressed={s.id === shopId}
              className={`h-9 cursor-pointer rounded-full px-3.5 text-[14px] transition-colors ${
                s.id === shopId ? "bg-ink font-medium text-ground" : "bg-raised text-ink hover:bg-active"
              }`}
            >
              {s.label}
            </button>
          ))}
          <button
            onClick={() => setNight(!night)}
            aria-pressed={night}
            className="ml-auto h-9 cursor-pointer rounded-full bg-raised px-3.5 text-[14px] hover:bg-active"
          >
            {night ? "Xem ban ngày" : "Xem lúc 23:47"}
          </button>
        </div>
        <div className="relative grid min-h-[520px] place-items-center overflow-hidden rounded-[var(--radius-sheet)] bg-raised p-4 sm:p-8">
          {shop.photo && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={shop.photo}
              src={shop.photo}
              alt={shop.alt}
              className="landing-fade absolute inset-0 size-full object-cover opacity-60"
            />
          )}
          <div className="relative w-full max-w-[420px]">
            <Messenger shop={shop} night={night} />
          </div>
          {shop.photo && <p className="absolute bottom-2 left-3 text-[13px] text-white/90 drop-shadow">{shop.alt}</p>}
        </div>
      </div>
    </section>
  );
}

const COMPARE: [string, string, string, string][] = [
  ["Khách nhắn lúc 23 giờ", "Nhận tin chờ, trả lời đủ lúc 8 giờ sáng", "Sáng hôm sau mới thấy", "Tuỳ ca trực"],
  ["Báo giá", "Chỉ lấy từ bảng giá bạn nhập", "Tra sổ, nhớ đâu nói đó", "Phải học thuộc bảng giá"],
  ["Câu hỏi khó, khiếu nại", "Chuyển cho bạn hoặc nhân viên xem", "Bạn tự xử lý", "Bạn tự xử lý"],
  ["Danh sách khách", "Tự lưu từ Messenger", "Ghi tay hoặc quên", "Ghi tay"],
  ["Lịch hẹn, nhiều chi nhánh", "Có, chặn trùng giờ", "Sổ hoặc điện thoại", "Sổ hoặc điện thoại"],
  ["Video quảng cáo 30 giây", "AI viết kịch bản, dựng video, lồng tiếng", "Tự quay, tự dựng", "Thuê ngoài"],
  ["Đăng Facebook, Instagram", "Lên lịch đăng sẵn", "Đăng tay từng bài", "Đăng tay từng bài"],
  ["Chi phí", "499.000đ một tháng", "Thời gian của bạn", "Một suất lương"],
];

function Compare() {
  return (
    <section id="tinh-nang" className="mx-auto max-w-[1240px] px-[20px] py-24 sm:px-8">
      <h2 data-reveal className="mb-12 text-[clamp(32px,3.4vw,46px)] font-semibold leading-tight">Một trợ lý, ba việc</h2>
      <div className="hidden md:block">
        <div className="relative grid grid-cols-[4fr_3fr_2.5fr_2.5fr]">
          <div aria-hidden className="absolute -top-6 left-[calc(4/12*100%)] h-6 w-[calc(3/12*100%)] rounded-t-[var(--radius-card)] bg-ink" />
          {[["", false], ["GrowthPilot", true], ["Tự trả lời tay", false], ["Thuê người trực page", false]].map(([t, hi]) => (
            <p key={String(t)} className={`relative px-5 pb-4 text-[17px] font-bold ${hi ? "bg-ink text-ground" : ""}`}>
              {t}
            </p>
          ))}
          {COMPARE.map((row, i) =>
            row.map((cell, j) => (
              <p
                key={`${i}-${j}`}
                className={`relative flex min-h-[68px] items-center px-5 ${j === 0 ? "text-[21px] font-medium" : "text-[17px]"} ${
                  j === 1 ? (i % 2 ? "bg-[#e4e1de] text-ground" : "bg-ink text-ground") : i % 2 ? "bg-surface" : ""
                } ${j === 1 && i === COMPARE.length - 1 ? "rounded-b-[var(--radius-card)]" : ""}`}
              >
                {cell}
              </p>
            )),
          )}
        </div>
      </div>
      <div className="flex flex-col gap-2 md:hidden">
        {COMPARE.map((row, i) => (
          <div key={i} className={`rounded-[var(--radius-card)] p-4 ${i % 2 ? "bg-surface" : "bg-raised"}`}>
            <p className="text-[20px] font-bold">{row[0]}</p>
            <p className="mt-2 rounded-md bg-ink px-3 py-2 text-ground">
              <b>GrowthPilot:</b> {row[1]}
            </p>
            <p className="mt-2">
              <span className="text-muted">Tự trả lời tay:</span> {row[2]}
            </p>
            <p className="mt-1">
              <span className="text-muted">Thuê người trực:</span> {row[3]}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

const PANELS = [
  {
    title: "Hộp thư",
    text: "Mọi tin nhắn Messenger ở một chỗ. AI gợi ý hoặc tự trả lời, bạn nhảy vào bất cứ lúc nào.",
    ui: (
      <div className="flex flex-col">
        {[
          ["Chị Thảo", "Bó hướng dương giao trưa mai được không…", "Đặt hàng", "positive"],
          ["Anh Minh", "Cà phê muối bao nhiêu vậy shop?", "Hỏi giá", "neutral"],
          ["Chị Vy", "Mình muốn đổi size áo đã mua hôm qua", "Cần người", "warning"],
        ].map(([n, t, tag, tone], i) => (
          <div key={n} className={`flex items-start gap-3 px-[20px] py-3 ${i ? "border-t border-border" : "bg-raised"}`}>
            <span className="grid size-8 flex-none place-items-center rounded-full bg-active text-[13px]">{n.split(" ")[1][0]}</span>
            <div className="min-w-0 flex-1">
              <p className="font-medium">{n}</p>
              <p className="truncate text-muted">{t}</p>
            </div>
            <span
              className="rounded-full px-2 py-0.5 text-[13px]"
              style={{ background: `var(--pill-${tone}-bg)`, color: `var(--pill-${tone}-ink)` }}
            >
              {tag}
            </span>
          </div>
        ))}
      </div>
    ),
  },
  {
    title: "Khách hàng",
    text: "Mỗi người từng nhắn tin thành một hồ sơ: đã hỏi gì, đã mua gì, lần cuối ghé khi nào.",
    ui: (
      <div className="p-4">
        <p className="text-[16px] font-semibold">Chị Thảo</p>
        <p className="text-muted">Messenger · khách từ 03/2026</p>
        <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
          <dt className="text-muted">Trạng thái</dt>
          <dd>Đã chốt đơn</dd>
          <dt className="text-muted">Đã mua</dt>
          <dd>3 lần · 1.250.000đ</dd>
          <dt className="text-muted">Ghi chú</dt>
          <dd>Thích hoa vàng, giao văn phòng</dd>
        </dl>
      </div>
    ),
  },
  {
    title: "Lịch hẹn",
    text: "Đặt lịch theo chi nhánh và sức chứa, không bao giờ nhận trùng hai khách một giờ.",
    ui: (
      <div className="p-4">
        <p className="mb-3 font-semibold">Thứ Bảy 14/11 · Chi nhánh Quận 3</p>
        {[
          ["09:00", "Sơn gel tay", "Chị Lan"],
          ["10:30", "Đắp gel + vẽ", "Chị Hà"],
          ["14:00", "Chăm sóc da tay", "Chị Ngọc"],
        ].map(([t, s, c]) => (
          <div key={t} className="flex gap-3 border-t border-border py-2">
            <span className="w-12 tabular-nums text-muted">{t}</span>
            <span className="flex-1">{s}</span>
            <span className="text-muted">{c}</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    title: "Video quảng cáo",
    text: "Viết một dòng mô tả, AI nghiên cứu, viết kịch bản 5 cảnh, dựng video dọc 30 giây có lồng tiếng Việt.",
    ui: (
      <div className="p-4">
        <p className="font-semibold">Kịch bản: Cà phê muối buổi sáng</p>
        {["Cận cảnh lớp kem muối rót lên ly", "Khách trẻ cầm ly đi ra ban công", "Chữ trên hình: 35.000đ, giao tận nơi", "Cảnh quán buổi sáng, nắng nhẹ", "Kêu gọi: nhắn Fanpage để đặt"].map((s, i) => (
          <p key={s} className="flex gap-3 border-t border-border py-2">
            <span className="text-muted tabular-nums">{i * 6}s</span>
            {s}
          </p>
        ))}
      </div>
    ),
  },
  {
    title: "Lịch đăng",
    text: "Đăng ảnh, video và Reels lên Facebook và Instagram cùng lúc, đúng giờ khách hay lướt.",
    ui: (
      <div className="p-4">
        {[
          ["T2 19:30", "Reels · Cà phê muối", "Instagram", "Đã đăng"],
          ["T4 11:45", "Ảnh · Menu mới", "Facebook", "Đã lên lịch"],
          ["T6 20:00", "Video 30s · Ưu đãi cuối tuần", "Cả hai", "Đã lên lịch"],
        ].map(([t, c, p, s]) => (
          <div key={t} className="grid grid-cols-[80px_1fr] gap-x-3 border-t border-border py-2 first:border-t-0">
            <span className="tabular-nums text-muted">{t}</span>
            <span>{c}</span>
            <span />
            <span className="text-muted">
              {p} · {s}
            </span>
          </div>
        ))}
      </div>
    ),
  },
];

function Showcase() {
  const [active, setActive] = useState(0);
  const p = PANELS[active];
  return (
    <section className="bg-black py-24">
      <div className="mx-auto grid max-w-[1240px] gap-10 px-[20px] sm:px-8 lg:grid-cols-[7fr_5fr] lg:items-center">
        <div data-ui className="landing-pop overflow-hidden rounded-xl bg-surface text-[14px]" key={active}>
          {p.ui}
        </div>
        <div>
          <h2 className="text-[clamp(28px,2.6vw,36px)] font-semibold">{p.title}</h2>
          <p className="mt-3 max-w-[40ch] text-[18px]">{p.text}</p>
          <div role="tablist" aria-label="Các phần của GrowthPilot" className="mt-8 flex flex-wrap gap-2">
            {PANELS.map((x, i) => (
              <button
                key={x.title}
                role="tab"
                aria-selected={i === active}
                onClick={() => setActive(i)}
                className={`h-9 cursor-pointer rounded-full px-3.5 text-[14px] ${i === active ? "bg-ink font-medium text-ground" : "bg-raised hover:bg-active"}`}
              >
                {x.title}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

const PHOTOS = [
  ["/landing/cafe.jpg", "Quán cafe ở phố cổ Hà Nội"],
  ["/landing/clothes.jpg", "Cửa hàng quần áo trên phố Hà Nội"],
  ["/landing/flowers.jpg", "Tiệm hoa ở quận 1, TP.HCM"],
  ["/landing/silk.jpg", "Tiệm lụa và tranh ở Hội An"],
  ["/landing/toys.jpg", "Hàng đồ chơi ở phố cổ Hà Nội"],
  ["/landing/lanterns.jpg", "Tiệm đèn lồng ở Hội An"],
];

function Shops() {
  return (
    <section className="mx-auto max-w-[1240px] px-[20px] py-24 sm:px-8">
      <div className="grid gap-6 lg:grid-cols-[5fr_7fr] lg:items-end">
        <h2 className="text-[clamp(32px,3.4vw,46px)] font-semibold leading-tight">Hợp với mọi cửa hàng</h2>
        <p className="text-[18px]">
          Quán ăn, cafe, shop quần áo, tiệm hoa, spa, tiệm nail, đồ lưu niệm. Bạn ghi loại hình kinh doanh và bảng giá, AI
          tư vấn đúng giọng và đúng ngành của bạn.
        </p>
      </div>
      <div className="mt-10 grid grid-cols-2 gap-2 lg:grid-cols-3">
        {PHOTOS.map(([src, cap], i) => (
          <figure key={src} data-reveal style={{ transitionDelay: `${(i % 3) * 80}ms` }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={src} alt={cap} loading="lazy" width={1600} height={1067} className="aspect-[4/3] size-full rounded-[var(--radius-card)] object-cover" />
            <figcaption className="mt-1.5 text-[14px] text-muted">{cap}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

function Steps() {
  return (
    <section className="mx-auto max-w-[1240px] px-[20px] py-24 sm:px-8">
      <h2 data-reveal className="mb-14 text-[clamp(28px,2.6vw,36px)] font-semibold">Bắt đầu trong 15 phút</h2>
      <ol className="flex max-w-[760px] flex-col gap-20">
        <li data-reveal>
          <p className="text-[20px] font-medium">Đầu tiên, nhập bảng giá.</p>
          <div className="mt-4 rounded-lg bg-surface p-5">
            <div data-ui className="grid grid-cols-[1fr_auto] gap-x-6 gap-y-2 text-[14px]">
              <span className="text-muted">Sản phẩm, dịch vụ</span>
              <span className="text-muted">Giá</span>
              <span>Cà phê muối</span>
              <span className="tabular-nums">35.000đ</span>
              <span>Bạc xỉu</span>
              <span className="tabular-nums">32.000đ</span>
              <span>Combo 2 ly + bánh</span>
              <span className="tabular-nums">79.000đ</span>
            </div>
          </div>
          <p className="ml-0 mt-4 rounded-lg bg-raised p-5 text-[15px] sm:ml-14">
            AI chỉ báo những giá có trong bảng. Giá nào không có, AI nói sẽ để nhân viên kiểm tra rồi báo bạn.
          </p>
        </li>
        <li data-reveal>
          <p className="text-[20px] font-medium">Sau đó, kết nối Fanpage.</p>
          <div className="mt-4 rounded-lg bg-surface p-5">
            <span data-ui className="inline-flex h-10 items-center rounded-md bg-[#1466d6] px-[20px] text-[14px] font-medium text-white">
              Kết nối Facebook & Instagram
            </span>
          </div>
          <div data-ui className="mt-4 flex flex-col gap-2 rounded-lg bg-raised p-5 text-[14px] sm:ml-14">
            <p className="flex justify-between">
              <span>Cà Phê Mộc · Facebook</span>
              <span className="text-[var(--pill-positive-ink)]">Đã kết nối</span>
            </p>
            <p className="flex justify-between">
              <span>@caphemoc · Instagram</span>
              <span className="text-[var(--pill-positive-ink)]">Đã kết nối</span>
            </p>
          </div>
        </li>
        <li data-reveal>
          <p className="text-[20px] font-medium">Cuối cùng, viết một dòng cho quảng cáo.</p>
          <div className="mt-4 rounded-lg bg-surface p-5 text-[15px]">
            Video 30 giây giới thiệu cà phê muối, khách văn phòng quận 1, giọng trẻ trung
          </div>
          <div className="mt-4 grid gap-4 rounded-lg bg-raised p-5 sm:grid-cols-[180px_1fr] xl:-mr-[300px]">
            <div data-ui className="flex aspect-[9/16] w-[180px] flex-col justify-between rounded-md bg-ground p-3 text-[13px]">
              <span className="self-start rounded bg-black/60 px-1.5 py-0.5">0:30 · 9:16</span>
              <span className="rounded bg-white px-2 py-1.5 text-center font-semibold text-black">Cà phê muối 35.000đ</span>
            </div>
            <div data-ui className="text-[14px]">
              <p className="font-semibold">Đã xong: 1 video 30 giây, 5 Reels ngắn, 3 ảnh đăng bài</p>
              <p className="mt-2 text-muted">Lồng tiếng Việt, chữ trên hình, nhạc nền. Bấm một nút để đăng hoặc lên lịch.</p>
              <div className="mt-4 flex gap-2">
                <span className="rounded-md bg-ink px-3 py-1.5 font-medium text-ground">Đăng ngay</span>
                <span className="rounded-md bg-active px-3 py-1.5">Lên lịch</span>
              </div>
            </div>
          </div>
        </li>
      </ol>
    </section>
  );
}

const PRICE_ROWS: [string, string, string][] = [
  ["Thời gian", "14 ngày", "Theo tháng, gia hạn bao lâu tuỳ bạn"],
  ["AI trả lời Messenger", "Có", "Có"],
  ["Khách hàng, lịch hẹn, chi nhánh", "Không giới hạn", "Không giới hạn"],
  ["Nhân viên dùng chung", "Không giới hạn", "Không giới hạn"],
  ["Video, ảnh quảng cáo", "Có", "Có"],
  ["Đăng Facebook, Instagram", "Có", "Có"],
  ["Thanh toán", "Không cần", "Chuyển khoản, quét VietQR"],
];

function Pricing() {
  return (
    <section id="bang-gia" className="mx-auto max-w-[1240px] px-[20px] py-24 sm:px-8">
      <div className="hidden md:grid md:grid-cols-[4fr_4fr_4fr]">
        <h2 className="self-end px-5 pb-6 text-[clamp(28px,2.6vw,36px)] font-semibold">Một giá, đủ tính năng</h2>
        <div className="px-5 pb-6">
          <p className="text-[2.6vw] font-bold leading-tight xl:text-[34px]">Dùng thử</p>
          <p className="text-[2.6vw] leading-tight xl:text-[34px]">0đ</p>
        </div>
        <div className="rounded-t-[var(--radius-card)] bg-accent px-5 pb-6 pt-5 text-[var(--accent-ink)]">
          <p className="text-[2.6vw] font-bold leading-tight xl:text-[34px]">Hàng tháng</p>
          <p className="text-[2.6vw] leading-tight xl:text-[34px]">
            499.000đ<span className="text-[16px]"> / tháng</span>
          </p>
        </div>
        {PRICE_ROWS.map(([k, a, b], i) => (
          <div key={k} className="contents">
            <p className={`px-5 py-5 text-[21px] ${i % 2 ? "" : "bg-surface"}`}>{k}</p>
            <p className={`px-5 py-5 text-[21px] ${i % 2 ? "" : "bg-surface"}`}>{a}</p>
            <p className={`bg-accent px-5 py-5 text-[21px] text-[var(--accent-ink)] ${i % 2 ? "" : "brightness-95"}`}>{b}</p>
          </div>
        ))}
        <span />
        <div className="px-5 pt-6">
          <Link href="/register" className="inline-flex h-12 items-center rounded-[var(--radius-control)] bg-ink px-6 font-medium text-ground hover:bg-ink/85">
            Bắt đầu dùng thử
          </Link>
        </div>
        <div className="rounded-b-[var(--radius-card)] bg-accent px-5 pb-6 pt-6">
          <Link href="/register" className="inline-flex h-12 items-center rounded-[var(--radius-control)] bg-ground px-6 font-medium text-ink hover:bg-ground/85">
            Dùng thử rồi trả sau
          </Link>
        </div>
      </div>
      <div className="flex flex-col gap-8 md:hidden">
        <h2 className="text-[9vw] font-semibold leading-tight">Một giá, đủ tính năng</h2>
        {[
          ["Dùng thử", "0đ", 1, false],
          ["Hàng tháng", "499.000đ / tháng", 2, true],
        ].map(([name, price, col, hi]) => (
          <div key={String(name)} className={`rounded-[var(--radius-card)] p-5 ${hi ? "bg-accent text-[var(--accent-ink)]" : "bg-surface"}`}>
            <p className="text-[8vw] font-bold leading-tight">{name}</p>
            <p className="text-[7vw]">{price}</p>
            <dl className="mt-4 flex flex-col gap-3 text-[17px]">
              {PRICE_ROWS.map((r) => (
                <div key={r[0]}>
                  <dt className="opacity-75">{r[0]}</dt>
                  <dd className="font-medium">{r[col as 1 | 2]}</dd>
                </div>
              ))}
            </dl>
            <Link href="/register" className={`mt-5 flex h-12 items-center justify-center rounded-[var(--radius-control)] font-medium ${hi ? "bg-ground text-ink" : "bg-ink text-ground"}`}>
              Bắt đầu dùng thử
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}

const FAQ = [
  ["Cửa hàng của tôi không phải spa, có dùng được không?", "Được. Quán ăn, cafe, shop quần áo, tiệm hoa, tiệm nail, đồ lưu niệm hay bất kỳ cửa hàng nào bán hàng qua Fanpage đều dùng được. Bạn ghi loại hình kinh doanh, AI tư vấn theo đúng ngành đó."],
  ["AI có tự bịa giá hoặc khuyến mãi không?", "Không. AI chỉ báo giá có trong bảng giá bạn nhập. Câu nào có giá lạ, khiếu nại hoặc chuyện nhạy cảm, AI dừng lại và báo bạn hoặc nhân viên vào trả lời."],
  ["Ban đêm khách nhắn thì sao?", "Ngoài giờ trực bạn đặt (mặc định 8:00 đến 22:00), khách nhận một tin cảm ơn và hẹn sáng mai. Đầu giờ sáng, AI đọc lại cả đêm và trả lời từng người một lần."],
  ["Hết 14 ngày dùng thử thì thế nào?", "Bạn chuyển khoản 499.000đ một tháng bằng mã VietQR trong trang Gói & thanh toán. Chưa gia hạn thì tin nhắn vẫn được lưu, chỉ AI tạm ngừng; gia hạn xong dùng tiếp, không mất dữ liệu."],
  ["Có cần thẻ ngân hàng hay biết kỹ thuật không?", "Không cần thẻ để dùng thử. Bạn chỉ cần tài khoản Facebook quản lý Fanpage; việc kết nối là bấm nút và chọn Page."],
  ["Có đăng được lên Instagram không?", "Có, nếu Instagram của bạn là tài khoản chuyên nghiệp và đã liên kết với Fanpage. Ảnh, video và Reels đăng được lên cả hai cùng lúc."],
  ["Dữ liệu khách của tôi có an toàn không?", "Mỗi cửa hàng chỉ thấy dữ liệu của mình, quyền nhân viên chia theo vai trò, mã truy cập Fanpage được mã hoá khi lưu. Bạn có thể xoá cửa hàng cùng toàn bộ dữ liệu bất cứ lúc nào."],
];

function Faq() {
  return (
    <section id="cau-hoi" className="mx-auto grid max-w-[1240px] gap-8 px-[20px] py-24 sm:px-8 lg:grid-cols-[4fr_8fr]">
      <h2 className="text-[clamp(32px,3.4vw,46px)] font-semibold leading-tight lg:sticky lg:top-24 lg:self-start">Câu hỏi hay gặp</h2>
      <div className="flex flex-col gap-2">
        {FAQ.map(([q, a]) => (
          <details data-reveal key={q} name="faq" className="group rounded-[var(--radius-card)] bg-surface open:bg-accent open:text-[var(--accent-ink)]">
            <summary className="flex min-h-[72px] cursor-pointer list-none items-center justify-between gap-4 px-6 py-4 text-[18px] font-medium [&::-webkit-details-marker]:hidden">
              {q}
              <span aria-hidden className="relative size-4 flex-none">
                <span className="absolute inset-x-0 top-1/2 h-[3px] -translate-y-1/2 rounded bg-current" />
                <span className="absolute inset-y-0 left-1/2 w-[3px] -translate-x-1/2 rounded bg-current transition-transform group-open:rotate-90" />
              </span>
            </summary>
            <p className="max-w-[60ch] px-6 pb-6 text-[17px]">{a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

function Cta() {
  const router = useRouter();
  const [name, setName] = useState("Cà Phê Mộc");
  const [kind, setKind] = useState("Quán cafe");
  function go(e: FormEvent) {
    e.preventDefault();
    router.push(`/register?${new URLSearchParams({ shop: name, industry: kind })}`);
  }
  return (
    <section className="bg-accent text-[var(--accent-ink)]">
      <div className="mx-auto grid min-h-[80svh] max-w-[1240px] items-center gap-10 px-[20px] py-20 sm:px-8 lg:grid-cols-2">
        <div className="self-end">
          <h2 className="text-[clamp(56px,7vw,104px)] font-semibold leading-[0.92]">
            Bắt đầu
            <br />
            hôm nay
          </h2>
          <p className="mt-5 max-w-[40ch] text-[17px]">
            Tạo tài khoản, nhập bảng giá và kết nối Fanpage. 14 ngày đầu miễn phí, không cần thẻ.
          </p>
        </div>
        <form onSubmit={go} data-ui className="w-full max-w-[440px] justify-self-end rounded-xl bg-surface p-6 text-ink shadow-2xl shadow-black/40">
          <p className="text-[18px] font-semibold">Tạo cửa hàng của bạn</p>
          <label className="mt-4 block text-[14px] font-medium" htmlFor="cta-name">
            Tên cửa hàng
          </label>
          <input
            id="cta-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1.5 h-10 w-full rounded-[var(--radius-control)] border border-control bg-ground px-3 text-[15px]"
          />
          <p className="mt-4 text-[14px] font-medium">Loại hình kinh doanh</p>
          <div className="mt-1.5 grid grid-cols-2 gap-1 rounded-[var(--radius-control)] bg-ground p-1 text-[14px]">
            {["Quán cafe", "Shop quần áo", "Tiệm hoa", "Spa, làm đẹp"].map((k) => (
              <button
                type="button"
                key={k}
                onClick={() => setKind(k)}
                aria-pressed={kind === k}
                className={`h-9 cursor-pointer rounded-md ${kind === k ? "bg-raised font-medium" : "text-muted hover:text-ink"}`}
              >
                {k}
              </button>
            ))}
          </div>
          <button type="submit" className="mt-6 h-12 w-full cursor-pointer rounded-[var(--radius-control)] bg-ink font-medium text-ground hover:bg-ink/85">
            Bắt đầu dùng thử 14 ngày
          </button>
        </form>
      </div>
    </section>
  );
}

/** Section parts rise in as they enter the screen. Hidden only once JS runs, so nothing is lost without it. */
function useReveal() {
  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const els = document.querySelectorAll<HTMLElement>("[data-reveal]");
    document.documentElement.classList.add("reveal-on");
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-in");
            io.unobserve(e.target);
          }
        }),
      { rootMargin: "0px 0px -10% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

export function Landing() {
  useReveal();
  return (
    <div className="min-h-screen bg-ground text-[16px]">
      <header className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-[20px] py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-2.5 font-semibold">
          <Mark size={28} /> GrowthPilot AI
        </Link>
        <nav className="flex items-center gap-5 text-[15px]">
          <a href="#tinh-nang" className="hidden hover:underline sm:inline">Tính năng</a>
          <a href="#bang-gia" className="hidden hover:underline sm:inline">Bảng giá</a>
          <a href="#cau-hoi" className="hidden hover:underline md:inline">Câu hỏi</a>
          <Link href="/login" className="hover:underline">Đăng nhập</Link>
          <Link href="/register" className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-ink px-[20px] font-medium text-ground hover:bg-ink/85">
            Dùng thử
          </Link>
        </nav>
      </header>
      <main>
        <Hero />
        <Compare />
        <Showcase />
        <Shops />
        <Steps />
        <Pricing />
        <Faq />
        <Cta />
      </main>
      <footer className="mx-auto mt-[20svh] grid max-w-[1240px] gap-2 px-[20px] pb-8 text-[14px] text-muted sm:px-8 md:grid-cols-[1fr_auto_1fr] md:items-baseline">
        <p>GrowthPilot AI · trợ lý bán hàng cho cửa hàng nhỏ</p>
        <LegalLinks />
        <p className="md:text-right">© 2026 GrowthPilot</p>
        <p className="text-[13px] md:col-span-3">
          Ảnh từ Wikimedia Commons: Alexkom000 (CC BY 4.0), Jakub Hałun (CC BY 4.0), Christophe95 (CC BY-SA 4.0), HappyMidnight
          (CC BY-SA 3.0), Fa2f (CC BY 3.0).
        </p>
      </footer>
    </div>
  );
}
