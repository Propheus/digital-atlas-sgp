import "./globals.css";

export const metadata = {
  title: "Alchemy — Singapore Spatial Intelligence",
  description:
    "Ask anything about Singapore's urban geography. Grounded in the Alchemy atlas — 332 subzones, 55 planning areas, places, demographics, walkability and commuter flows.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
