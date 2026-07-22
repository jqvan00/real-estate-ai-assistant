import "./globals.css";

export const metadata = {
  title: "AI Real Estate Showing Assistant",
  description: "Verified property profile and AI analysis starter.",
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
