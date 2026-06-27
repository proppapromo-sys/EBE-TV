import "./globals.css";
import Nav from "../components/Nav";

export const metadata = { title: "EBE-TV", description: "Watch original shows" };

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
