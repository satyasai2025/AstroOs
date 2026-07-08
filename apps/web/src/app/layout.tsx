import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: "AstroOS — Vedic Astrology Research Platform",
    template: "%s | AstroOS",
  },
  description:
    "A production-grade Vedic Astrology research platform for scholars, practitioners, and researchers.",
  keywords: ["Vedic Astrology", "Jyotish", "Horoscope", "Ephemeris", "Research"],
  authors: [{ name: "AstroOS" }],
  robots: "noindex, nofollow", // Private research platform
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
