import { useRef, useState } from 'react';
import Card from '../ui/Card.jsx';
import Spinner from '../ui/Spinner.jsx';
import StatusPill from '../ui/StatusPill.jsx';
import ErrorBanner from '../ui/ErrorBanner.jsx';
import { UploadCloudIcon } from '../icons.jsx';
import { DROPZONE_ACCEPT } from '../../utils/files.js';

const FORMAT_CHIPS = ['PDF', 'PNG', 'JPG', 'JPEG', 'WEBP'];

export default function UploadCard({ variant = 'hero', upload, onFileSelected }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const isUploading = upload.status === 'uploading';
  const isProcessing = isUploading && upload.progress >= 100;
  const isHero = variant === 'hero';

  const openPicker = () => {
    if (!isUploading) inputRef.current?.click();
  };

  const handleInputChange = (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (file) onFileSelected(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    if (isUploading) return;
    const file = event.dataTransfer.files?.[0];
    if (file) onFileSelected(file);
  };

  return (
    <Card
      className={`upload-card upload-card--${variant}`}
      title={isHero ? undefined : 'Document upload'}
      actions={
        !isHero && upload.status === 'success' ? (
          <StatusPill tone="success">Uploaded</StatusPill>
        ) : undefined
      }
    >
      <div
        className={`dropzone dropzone--${variant}${isDragging ? ' dropzone--dragging' : ''}${
          isUploading ? ' dropzone--busy' : ''
        }`}
        role="button"
        tabIndex={0}
        aria-disabled={isUploading}
        onClick={openPicker}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openPicker();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          if (!isUploading) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={DROPZONE_ACCEPT}
          hidden
          onChange={handleInputChange}
        />
        {isUploading ? (
          <div className="dropzone__progress" aria-live="polite">
            <Spinner size={18} />
            <p className="dropzone__headline">
              {isProcessing ? 'Processing document…' : 'Uploading document…'}
            </p>
            {isProcessing ? (
              <p className="dropzone__hint">The server is parsing and indexing your file.</p>
            ) : (
              <>
                <div
                  className="progress"
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={upload.progress}
                >
                  <div className="progress__bar" style={{ width: `${upload.progress}%` }} />
                </div>
                <p className="dropzone__percent">{upload.progress}%</p>
              </>
            )}
          </div>
        ) : (
          <>
            <span className="dropzone__icon">
              <UploadCloudIcon size={isHero ? 26 : 20} />
            </span>
            <p className="dropzone__headline">
              {isHero ? 'Drag & drop a document to analyze' : 'Upload another document'}
            </p>
            <p className="dropzone__hint">
              {isHero ? 'or click to browse your files' : 'Drag a file here or click to browse'}
            </p>
            {isHero && (
              <div className="dropzone__chips">
                {FORMAT_CHIPS.map((format) => (
                  <span key={format} className="chip">
                    {format}
                  </span>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {upload.status === 'error' && (
        <ErrorBanner title="Upload failed" message={upload.error} onRetry={openPicker} retryLabel="Choose file" />
      )}

      <p className="upload-card__footnote">Supported formats: PDF, PNG, JPG, JPEG, WEBP · Max size 25 MB</p>
    </Card>
  );
}
