import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { ThemeToggle } from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "SKLab Studio",
  description: "Run agents. Watch progress. Verify results.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <header className="border-b border-zinc-800">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <div>
              <div className="text-lg font-semibold tracking-tight">SKLab Studio</div>
              <div className="text-xs text-zinc-400">AI Engineering Workstation</div>
            </div>
            <ThemeToggle />
          </div>
          <Nav />
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
