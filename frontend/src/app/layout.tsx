import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StartupTracker",
  description: "Track startup funding rounds and investors",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
