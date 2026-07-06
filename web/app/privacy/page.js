export const metadata = { title: "Privacy Policy — EBE·TV" };

export default function Privacy() {
  return (
    <main className="wrap legal" style={{ maxWidth: 760 }}>
      <h1>Privacy Policy</h1>
      <p className="muted">Last updated: 2026. EBE TECHNOLOGIES INC (“EBE·TV”, “we”).</p>
      <p className="muted" style={{ fontStyle: "italic" }}>
        Template for launch — have counsel review before relying on it.</p>

      <h2>What we collect</h2>
      <p>Account info (email, display name), subscription &amp; billing status, and viewing activity
        (what you watch and your progress) to power continue-watching and recommendations.</p>

      <h2>How we use it</h2>
      <p>To run your account, process payments, stream video, personalize rows, send service email
        (receipts, password resets), and keep the platform secure.</p>

      <h2>Who we share it with</h2>
      <p>Service providers that make EBE·TV work: <b>Stripe</b> (payments), <b>Cloudflare</b>
        (video delivery &amp; DRM), <b>Resend</b> (email), and our hosting. We don’t sell your
        personal data.</p>

      <h2>Your choices</h2>
      <p>You can update or delete your account and cancel your subscription from the Account page.
        Email <b>privacy@ebe.tv</b> to request a copy or deletion of your data.</p>

      <h2>Payment data</h2>
      <p>Card details are handled by Stripe and never stored on our servers.</p>

      <h2>Contact</h2>
      <p>privacy@ebe.tv</p>
    </main>
  );
}
