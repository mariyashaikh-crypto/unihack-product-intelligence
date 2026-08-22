import { AlertTriangleIcon, RefreshIcon } from '../icons.jsx';

export default function ErrorBanner({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
}) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-banner__icon">
        <AlertTriangleIcon size={18} />
      </span>
      <div className="error-banner__content">
        <p className="error-banner__title">{title}</p>
        {message && <p className="error-banner__message">{message}</p>}
      </div>
      {onRetry && (
        <button type="button" className="btn btn--ghost btn--sm" onClick={onRetry}>
          <RefreshIcon size={14} />
          {retryLabel}
        </button>
      )}
    </div>
  );
}
