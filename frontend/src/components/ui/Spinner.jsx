export default function Spinner({ size = 16, className = '' }) {
  return (
    <span
      className={`spinner ${className}`.trim()}
      style={{ width: size, height: size }}
      aria-hidden="true"
    />
  );
}
