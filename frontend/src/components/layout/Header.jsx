import { FilePlusIcon, MenuIcon } from '../icons.jsx';
import StatusPill from '../ui/StatusPill.jsx';

const STATUS_PILL = {
  checking: { tone: 'neutral', label: 'Checking backend…' },
  online: { tone: 'success', label: 'Backend online' },
  offline: { tone: 'danger', label: 'Backend offline' },
};

export default function Header({ onMenuClick, connection, hasActiveDoc = false, onNewDocument }) {
  const status = STATUS_PILL[connection] ?? STATUS_PILL.checking;

  return (
    <header className="header">
      <div className="header__left">
        <button
          type="button"
          className="icon-btn header__menu"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <MenuIcon size={20} />
        </button>
        <div className="header__titles">
          <h1 className="header__title">Dashboard</h1>
          <p className="header__subtitle">Upload product documents and ask questions about them</p>
        </div>
      </div>
      <div className="header__right">
        {hasActiveDoc && (
          <button
            type="button"
            className="btn btn--ghost btn--sm header__new-doc"
            onClick={onNewDocument}
            aria-label="New document"
          >
            <FilePlusIcon size={14} />
            <span>New document</span>
          </button>
        )}
        <StatusPill tone={status.tone}>{status.label}</StatusPill>
      </div>
    </header>
  );
}
