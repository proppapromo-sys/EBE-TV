// EBE·TV mark — an original broadcast "signal" glyph (a source dot emitting arcs) in the
// house violet→gold gradient. Not a play triangle, not anyone else's logo.
export default function BrandMark({ className = "brandmark" }) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="url(#ebe)" />
      <circle cx="11" cy="21" r="2.6" fill="#fff" />
      <path d="M11 15.5a5.5 5.5 0 0 1 5.5 5.5" stroke="#fff" strokeWidth="2.3"
            strokeLinecap="round" />
      <path d="M11 11a10 10 0 0 1 10 10" stroke="#fff" strokeWidth="2.3"
            strokeLinecap="round" opacity="0.85" />
      <defs>
        <linearGradient id="ebe" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7a5cff" />
          <stop offset="1" stopColor="#ffc857" />
        </linearGradient>
      </defs>
    </svg>
  );
}
