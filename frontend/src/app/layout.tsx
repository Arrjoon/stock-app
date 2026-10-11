import type { ReactNode } from "react";
import type { Metadata } from "next";
import { Urbanist } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";
import Providers from "@/providers/Providers";

import "./globals.css";

const sans = Urbanist({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "NEPSE Stock App",
  description: "Role-gated NEPSE market, news, and analysis dashboard.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${sans.className}`}>
      <body className="min-h-screen antialiased">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
