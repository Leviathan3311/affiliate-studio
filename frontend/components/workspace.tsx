"use client";

import { useRouter } from "next/navigation";
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
  if (!session.token()) return "login";
  const me = await api<Me>("/auth/me");
  const current = me.workspaces.find((w) => w.id === session.workspace()) ?? me.workspaces[0];
  if (!current) return "onboarding";
  session.setWorkspace(current.id);
  return { me, workspace: await api<Workspace>("/workspace") };
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
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

  if (!state) {
    return (
      <div className="grid min-h-screen place-items-center text-sm text-muted" role="status">
        Đang tải workspace…
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
