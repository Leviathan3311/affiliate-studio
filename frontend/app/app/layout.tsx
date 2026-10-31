import { Shell } from "@/components/shell";
import { WorkspaceProvider } from "@/components/workspace";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <Shell>{children}</Shell>
    </WorkspaceProvider>
  );
}
