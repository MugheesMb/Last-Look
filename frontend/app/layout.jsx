import { Fraunces, Inter, IBM_Plex_Mono, Caveat } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["400", "500", "600"],
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-plex-mono",
  weight: ["400", "500", "600"],
});

const caveat = Caveat({
  subsets: ["latin"],
  variable: "--font-script",
  weight: ["500", "600"],
});

export const metadata = {
  title: "LastLook",
  description: "AI skin analysis and color-verified outfits, built around the days you actually have.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${inter.variable} ${plexMono.variable} ${caveat.variable}`}>
      <body>{children}</body>
    </html>
  );
}
