import "./globals.css";
import Nav from "../components/Nav";

export const metadata = {
  title: "EBE·TV — Original shows, all access",
  description: "EBE·TV: original series and live events. One subscription, every show.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        {children}
      </body>
    </html>
  );
}
