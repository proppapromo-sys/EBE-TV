import "./globals.css";

export const metadata = { title: "Streaming", description: "Watch original shows" };

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <a className="brand" href="/">▶ STREAM</a>
          <a href="/" className="muted">Browse</a>
          <a href="/subscribe" className="muted">Subscribe</a>
          <span className="spacer" />
          <a href="/login" className="btn ghost">Sign in</a>
        </nav>
        {children}
      </body>
    </html>
  );
}
