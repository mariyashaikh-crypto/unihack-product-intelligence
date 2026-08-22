import { useRef, useState } from 'react';
import Card from '../ui/Card.jsx';
import StatusPill from '../ui/StatusPill.jsx';
import {
  CheckIcon,
  CopyIcon,
  ExternalLinkIcon,
  FilePlusIcon,
  FileTextIcon,
  RefreshIcon,
} from '../icons.jsx';
import { getDocumentFileUrl } from '../../api/client.js';
import { detectFileKind, fileTypeLabel } from '../../utils/files.js';
import { formatBytes, formatDateTime } from '../../utils/format.js';

export default function DocumentInfoCard({ doc, onReplace, onNewDocument }) {
  const inputRef = useRef(null);
  const [copied, setCopied] = useState(false);

  const kind = detectFileKind({ contentType: doc.contentType, filename: doc.filename });
  const fileUrl = doc.fileUrl ?? (doc.id ? getDocumentFileUrl(doc.id) : null);
  const hasStats = doc.pages !== null || doc.chunks !== null || doc.visualOnly !== null;

  const handleCopy = async () => {
    if (!doc.id) return;
    try {
      await navigator.clipboard.writeText(String(doc.id));
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  const handleReplaceChange = (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (file) onReplace(file);
  };

  return (
    <Card
      className="doc-info-card"
      title="Document information"
      actions={<StatusPill tone="success">Ready</StatusPill>}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp"
        hidden
        onChange={handleReplaceChange}
      />

      <div className="doc-preview">
        {kind === 'image' && fileUrl ? (
          <img className="doc-preview__image" src={fileUrl} alt={doc.filename} />
        ) : (
          <div className="doc-preview__placeholder">
            <FileTextIcon size={26} />
            <span>{kind === 'pdf' ? 'PDF document' : 'Document'}</span>
            {fileUrl && (
              <a className="doc-preview__link" href={fileUrl} target="_blank" rel="noreferrer">
                Open file <ExternalLinkIcon size={13} />
              </a>
            )}
          </div>
        )}
      </div>

      {hasStats && (
        <div className="doc-stats">
          {doc.pages !== null && (
            <span className="doc-stats__item">
              <span className="doc-stats__value">{doc.pages}</span> page{doc.pages === 1 ? '' : 's'}
            </span>
          )}
          {doc.chunks !== null && (
            <span className="doc-stats__item">
              <span className="doc-stats__value">{doc.chunks}</span> chunk{doc.chunks === 1 ? '' : 's'}
            </span>
          )}
          {doc.visualOnly !== null && (
            <span className="doc-stats__item">
              {doc.visualOnly ? 'Visual only' : 'Readable text'}
            </span>
          )}
        </div>
      )}

      <dl className="doc-meta">
        <div className="doc-meta__row">
          <dt>Filename</dt>
          <dd title={doc.filename}>{doc.filename}</dd>
        </div>
        <div className="doc-meta__row">
          <dt>Format</dt>
          <dd>{fileTypeLabel({ contentType: doc.contentType, filename: doc.filename })}</dd>
        </div>
        <div className="doc-meta__row">
          <dt>Size</dt>
          <dd>{formatBytes(doc.size)}</dd>
        </div>
        <div className="doc-meta__row">
          <dt>Uploaded</dt>
          <dd>{formatDateTime(doc.uploadedAt)}</dd>
        </div>
        <div className="doc-meta__row">
          <dt>Document ID</dt>
          <dd className="doc-meta__id">
            <span className="doc-meta__id-value" title={doc.id ? String(doc.id) : undefined}>
              {doc.id ? String(doc.id) : '—'}
            </span>
            {doc.id && (
              <button
                type="button"
                className="icon-btn icon-btn--xs"
                onClick={handleCopy}
                aria-label="Copy document id"
              >
                {copied ? <CheckIcon size={13} /> : <CopyIcon size={13} />}
              </button>
            )}
          </dd>
        </div>
      </dl>

      <div className="doc-info-card__actions">
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={() => inputRef.current?.click()}
        >
          <RefreshIcon size={14} /> Replace file
        </button>
        <button type="button" className="btn btn--primary btn--sm" onClick={onNewDocument}>
          <FilePlusIcon size={14} /> New document
        </button>
      </div>
    </Card>
  );
}
