export const ACCEPTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.webp'];

export const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/webp',
];

export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;

export const DROPZONE_ACCEPT = [...ACCEPTED_EXTENSIONS, ...ACCEPTED_MIME_TYPES].join(',');

export function getFileExtension(filename) {
  if (!filename || !filename.includes('.')) return '';
  return filename.slice(filename.lastIndexOf('.')).toLowerCase();
}

export function detectFileKind({ contentType, filename } = {}) {
  const extension = getFileExtension(filename);
  if (contentType === 'application/pdf' || extension === '.pdf') return 'pdf';
  if (
    (contentType && contentType.startsWith('image/')) ||
    ['.png', '.jpg', '.jpeg', '.webp'].includes(extension)
  ) {
    return 'image';
  }
  return 'other';
}

export function fileTypeLabel({ contentType, filename } = {}) {
  const extension = getFileExtension(filename);
  if (extension) return extension.replace('.', '').toUpperCase();
  if (contentType) return contentType.split('/').pop().toUpperCase();
  return 'FILE';
}

export function validateFile(file) {
  if (!file) return { ok: false, error: 'No file was selected.' };

  const extension = getFileExtension(file.name);
  const mimeOk = file.type && ACCEPTED_MIME_TYPES.includes(file.type);
  const extensionOk = ACCEPTED_EXTENSIONS.includes(extension);

  if (!mimeOk && !extensionOk) {
    return {
      ok: false,
      error: 'Unsupported file type. Please upload a PDF, PNG, JPG, JPEG or WEBP file.',
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { ok: false, error: 'File is too large. The maximum size is 25 MB.' };
  }

  if (file.size === 0) {
    return { ok: false, error: 'The selected file is empty.' };
  }

  return { ok: true };
}
