import type { PropsWithChildren } from 'react';

export function AppShell({ children }: PropsWithChildren) {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>UP Bus Tracker</h1>
          <p>Fleet operations console</p>
        </div>
      </header>
      {children}
    </main>
  );
}

