export default function StatusPill({ tone = 'neutral', children, className = '' }) {
  const toneClass = `pill--${tone}`;
  return <span className={`pill ${toneClass} ${className}`.trim()}>{children}</span>;
}
