import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitPlan AI",
  description: "Adaptive AI workout scheduling assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
