"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, session } from "@/lib/api";
import type { Me, Workspace } from "@/lib/types";

interface Ctx {
  me: Me;
  workspace: Workspace;
  reload: () => Promise<void>;
  can: (...roles: string[]) => boolean;
}

const WorkspaceContext = createContext<Ctx | null>(null);

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace outside WorkspaceProvider");
  return ctx;
}

type State = { me: Me; workspace: Workspace };

async function loadState(): Promise<State | "login" | "onboarding"> {
  if (!session.signedIn()) return "login";
  const me = await api<Me>("/auth/me");
  const current = me.workspaces.find((w) => w.id === session.workspace()) ?? me.workspaces[0];
  if (!current) return "onboarding";
  session.setWorkspace(current.id);
  return { me, workspace: await api<Workspace>("/workspace") };
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<State | null>(null);

  const load = useCallback(async () => {
    const next = await loadState().catch(() => "login" as const);
    if (typeof next === "string") router.replace(`/${next}`);
    else setState(next);
  }, [router]);

  useEffect(() => {
    loadState()
      .catch(() => "login" as const)
      .then((next) => (typeof next === "string" ? router.replace(`/${next}`) : setState(next)));
  }, [router]);

  // A platform admin can extend any shop's plan: enrol the second factor before anything else.
  const mustEnrol = state?.me.is_platform_admin && !state.me.mfa_enabled && pathname !== "/app/admin";
  useEffect(() => {
    if (mustEnrol) router.replace("/app/admin");
  }, [mustEnrol, router]);
  if (!state || mustEnrol) {
    return (
      <div className="grid min-h-screen place-items-center text-sm text-muted" role="status">
        Đang tải…
      </div>
    );
  }
  const role = state.workspace.role;
  return (
    <WorkspaceContext.Provider
      value={{ ...state, reload: load, can: (...roles) => role === "owner" || roles.includes(role) }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}
