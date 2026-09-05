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
        <div className="scanlines" aria-hidden="true" />
        <header className="border-b border-zinc-800">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
            <div>
              <div className="phos text-lg font-semibold tracking-tight">SKLab://WORKSTATION</div>
              <div className="eyebrow mt-1">single-user control center / v0.4</div>
            </div>
            <ThemeToggle />
          </div>
          <Nav />
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
