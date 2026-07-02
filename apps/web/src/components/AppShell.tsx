import type { ReactNode } from "react";
import { Landmark } from "lucide-react";

type AppShellProps = {
  parserCount: number;
  sidebarCollapsed: boolean;
  children: ReactNode;
};

export function AppShell({ parserCount, sidebarCollapsed, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand-lockup">
          <h1 className="sr-only">Kasa</h1>
          <img className="brand-logo" src="/kasa-logo.svg" alt="Kasa" />
          <span>Statement parser</span>
        </div>
        <div className="parser-count">
          <Landmark aria-hidden="true" size={16} />
          {parserCount} supported parser{parserCount === 1 ? "" : "s"}
        </div>
      </header>
      <main className={`workspace${sidebarCollapsed ? " is-panel-collapsed" : ""}`}>
        {children}
      </main>
    </div>
  );
}
