import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { ThemeProvider } from "@/components/layout/ThemeProvider";

// Google Fonts: Outfit (headings), Inter (body UI), JetBrains Mono (code)
const fontHeadings = "https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap";
const fontBody = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap";
const fontMono = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap";

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
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        {/* Google Fonts Preconnect */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* Font stylesheets */}
        <link href={fontHeadings} rel="stylesheet" />
        <link href={fontBody} rel="stylesheet" />
        <link href={fontMono} rel="stylesheet" />
      </head>
      <body>
        <ThemeProvider>
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
