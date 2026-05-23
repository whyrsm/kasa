import type { ReactNode } from "react";

type AppShellProps = {
  parserCount: number;
  children: ReactNode;
};

export function AppShell({ parserCount, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          <h1>Kasa</h1>
          <span>Statement parser</span>
        </div>
        <div className="parser-count">Parsers: {parserCount} supported</div>
      </header>
      <main className="workspace">{children}</main>
    </div>
  );
}
