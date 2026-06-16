import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "AI Scraper Engine — Intelligent Web Scraping",
  description:
    "AI-powered web scraping chatbot. Describe what data you need, and let AI build the scraping pipeline for you.",
  keywords: ["web scraping", "AI", "data extraction", "automation"],
};
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}