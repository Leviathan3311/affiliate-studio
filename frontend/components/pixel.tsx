"use client";

import Script from "next/script";

/** Meta Pixel for the ads that bring new shops in. Off unless NEXT_PUBLIC_META_PIXEL_ID is set at build time. */
const ID = process.env.NEXT_PUBLIC_META_PIXEL_ID;

type Fbq = (cmd: "track", event: string, params?: Record<string, unknown>) => void;

export function track(event: string, params?: Record<string, unknown>) {
  const fbq = (window as unknown as { fbq?: Fbq }).fbq;
  if (ID && fbq) fbq("track", event, params);
}

export function MetaPixel() {
  if (!ID || !/^\d+$/.test(ID)) return null;
  return (
    <Script id="meta-pixel" strategy="afterInteractive">
      {`!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${ID}');fbq('track','PageView');`}
    </Script>
  );
}
