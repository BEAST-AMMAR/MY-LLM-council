import type { Metadata } from "next";
import { Exo_2, Outfit } from "next/font/google";
import "./globals.css";

const exo2 = Exo_2({ subsets: ["latin"], variable: "--font-exo" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "LLM Council v4.0 | Multi-Agent Deliberation",
  description: "Multi-agent LLM council powered by hybrid cloud and local inference.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${exo2.variable} ${outfit.variable} antialiased bg-[#04040f] text-[#e0eeff]`}>
        {children}
      </body>
    </html>
  );
}
