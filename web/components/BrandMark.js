// EBE·TV mark — a vector echo of the brand emblem: a chrome ring around a rising skyline
// over a wave with a star. Rendered in a brushed-silver gradient.
export default function BrandMark({ className = "brandmark" }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="ebeChrome" x1="12" y1="6" x2="52" y2="60" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f5f8fc" />
          <stop offset="0.5" stopColor="#bcc6d4" />
          <stop offset="1" stopColor="#838e9e" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="28" stroke="url(#ebeChrome)" strokeWidth="3" />
      {/* rising skyline */}
      <g fill="url(#ebeChrome)">
        <rect x="20" y="29" width="6.5" height="16" rx="1.2" />
        <rect x="28.5" y="18" width="7" height="27" rx="1.2" />
        <rect x="37.5" y="24" width="6.5" height="21" rx="1.2" />
      </g>
      {/* wave */}
      <path d="M15 51 C 23 47, 30 54, 38 50 C 44 47.5, 49 50, 51 49"
            stroke="url(#ebeChrome)" strokeWidth="2.6" strokeLinecap="round" />
      {/* star */}
      <path transform="translate(43 50)"
            d="M0 -5.5 L1.24 -1.7 5.23 -1.7 2 0.65 3.24 4.45 0 2.1 -3.24 4.45 -2 0.65 -5.23 -1.7 -1.24 -1.7 Z"
            fill="url(#ebeChrome)" />
    </svg>
  );
}
