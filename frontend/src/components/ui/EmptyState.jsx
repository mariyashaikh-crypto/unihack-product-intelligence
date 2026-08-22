export default function EmptyState({ icon, title, description, children, className = '' }) {
  return (
    <section className={`empty-state ${className}`.trim()}>
      {icon && <div className="empty-state__icon">{icon}</div>}
      {title && <h2 className="empty-state__title">{title}</h2>}
      {description && <p className="empty-state__description">{description}</p>}
      {children}
    </section>
  );
}
