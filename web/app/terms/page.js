export const metadata = { title: "Terms of Use — EBE·TV" };

export default function Terms() {
  return (
    <main className="wrap legal" style={{ maxWidth: 760 }}>
      <h1>Terms of Use</h1>
      <p className="muted">Last updated: 2026. EBE TECHNOLOGIES INC (“EBE·TV”, “we”).</p>
      <p className="muted" style={{ fontStyle: "italic" }}>
        Template for launch — have counsel review before relying on it.</p>

      <h2>1. Your account</h2>
      <p>You’re responsible for your login and for activity under it. You must be old enough to form
        a binding contract in your jurisdiction to subscribe.</p>

      <h2>2. Subscriptions &amp; billing</h2>
      <p>EBE·TV is a paid subscription. Web subscriptions are billed through Stripe on a recurring
        basis until canceled. You can cancel anytime from your Account page; access continues
        through the end of the paid period. Subscriptions purchased in a mobile app are billed and
        canceled through that app store.</p>

      <h2>3. License &amp; acceptable use</h2>
      <p>We grant you a personal, non-transferable license to stream content for non-commercial use.
        You may not copy, record, redistribute, or circumvent the DRM protecting our video.</p>

      <h2>4. Creator content</h2>
      <p>Creators retain ownership of what they upload and grant EBE·TV a license to host and stream
        it. Creators are paid per the payout terms shown in the Creator dashboard. Uploaded content
        must be lawful and rights-cleared.</p>

      <h2>5. Termination &amp; changes</h2>
      <p>We may suspend accounts that violate these terms, and may update the service or these terms
        with notice. Continued use means you accept the changes.</p>

      <h2>6. Contact</h2>
      <p>Questions: support@ebe.tv</p>
    </main>
  );
}
