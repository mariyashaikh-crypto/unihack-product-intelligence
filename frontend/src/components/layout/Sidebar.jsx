import { ChatIcon, CloseIcon, FileTextIcon, ImageIcon, RefreshIcon, SparklesIcon } from '../icons.jsx';
import { detectFileKind } from '../../utils/files.js';
import { timeAgo } from '../../utils/format.js';

const CONNECTION_LABELS = {
  checking: 'Checking connection…',
  online: 'Connected',
  offline: 'Offline',
};

function documentSubtitle(doc) {
  const relative = timeAgo(doc.uploadedAt);
  if (relative) return relative;
  if (doc.pages !== null) return `${doc.pages} page${doc.pages === 1 ? '' : 's'}`;
  return 'Uploaded';
}

export default function Sidebar({
  isOpen,
  onClose,
  documents,
  activeDocumentId,
  onSelectDocument,
  onRetryLoad,
  connection,
}) {
  return (
    <>
      <aside className={`sidebar${isOpen ? ' sidebar--open' : ''}`}>
        <div className="sidebar__brand">
          <span className="brand-mark">
            <SparklesIcon size={17} />
          </span>
          <span className="brand-text">
            <span className="brand-name">Product Intelligence</span>
            <span className="brand-sub">Document console</span>
          </span>
          <button
            type="button"
            className="icon-btn sidebar__close"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <CloseIcon size={16} />
          </button>
        </div>

        <nav className="sidebar__section" aria-label="Workspace">
          <p className="sidebar__label">Workspace</p>
          <button type="button" className="nav-item nav-item--active">
            <ChatIcon size={15} />
            Dashboard
          </button>
        </nav>

        <div className="sidebar__section sidebar__section--grow">
          <div className="sidebar__label-row">
            <p className="sidebar__label">Documents</p>
            {documents.status === 'ready' && (
              <span className="count-pill">{documents.items.length}</span>
            )}
            <button
              type="button"
              className="icon-btn icon-btn--xs sidebar__refresh"
              onClick={onRetryLoad}
              aria-label="Refresh document list"
              title="Refresh document list"
            >
              <RefreshIcon size={13} />
            </button>
          </div>

          {documents.status === 'loading' && (
            <div className="doc-list">
              {[0, 1, 2].map((index) => (
                <span key={index} className="skeleton doc-list-skeleton" />
              ))}
            </div>
          )}

          {documents.status === 'error' && (
            <div className="sidebar-note">
              <p>Could not load documents.</p>
              <button type="button" className="btn btn--ghost btn--xs" onClick={onRetryLoad}>
                Retry
              </button>
            </div>
          )}

          {documents.status === 'ready' && documents.items.length === 0 && (
            <p className="sidebar-note">No documents yet. Upload one to get started.</p>
          )}

          {documents.status === 'ready' && documents.items.length > 0 && (
            <ul className="doc-list">
              {documents.items.map((doc) => {
                const kind = detectFileKind({
                  contentType: doc.contentType,
                  filename: doc.filename,
                });
                const isActive = doc.id !== null && doc.id === activeDocumentId;
                return (
                  <li key={doc.id ?? doc.filename}>
                    <button
                      type="button"
                      className={`doc-item${isActive ? ' doc-item--active' : ''}`}
                      onClick={() => onSelectDocument(doc)}
                      title={doc.filename}
                    >
                      <span className="doc-item__icon">
                        {kind === 'pdf' ? <FileTextIcon size={15} /> : <ImageIcon size={15} />}
                      </span>
                      <span className="doc-item__meta">
                        <span className="doc-item__name">{doc.filename}</span>
                        <span className="doc-item__time">{documentSubtitle(doc)}</span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <footer className="sidebar__footer">
          <div className="connection-card">
            <span className={`connection-dot connection-dot--${connection}`} />
            <span className="connection-text">
              <span className="connection-title">Backend API</span>
              <span className="connection-sub">
                {CONNECTION_LABELS[connection] ?? 'Unknown'}
              </span>
            </span>
          </div>
        </footer>
      </aside>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} aria-hidden="true" />}
    </>
  );
}
