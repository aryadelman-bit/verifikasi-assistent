import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Validator PDF IntraNEW",
  description: "Validasi lokal laporan PDF IntraNEW berbasis aturan."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}

