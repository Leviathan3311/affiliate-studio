import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";
import { MetaPixel } from "@/components/pixel";
import "./globals.css";

const plex = IBM_Plex_Sans({
  variable: "--font-plex",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "GrowthPilot AI · AI trả lời khách và làm quảng cáo cho cửa hàng",
  description:
    "AI trả lời tin nhắn Facebook bằng bảng giá của cửa hàng bạn, quản lý khách, lịch hẹn và tự làm video quảng cáo cho Facebook, Instagram. Dùng thử 14 ngày miễn phí.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" className={`${plex.variable} h-full antialiased`}>
      <body className="min-h-full">
        {children}
        <MetaPixel />
      </body>
    </html>
  );
}
