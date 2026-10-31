"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { session } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(session.token() ? "/app" : "/login");
  }, [router]);
  return null;
}
