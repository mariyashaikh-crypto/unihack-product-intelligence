export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(Number(bytes))) return '—';
  const value = Number(bytes);
  if (value < 1024) return `${value} B`;
  const units = ['KB', 'MB', 'GB'];
  let scaled = value / 1024;
  let unitIndex = 0;
  while (scaled >= 1024 && unitIndex < units.length - 1) {
    scaled /= 1024;
    unitIndex += 1;
  }
  return `${scaled >= 100 ? Math.round(scaled) : scaled.toFixed(1)} ${units[unitIndex]}`;
}

export function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export function timeAgo(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 45) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, { dateStyle: 'medium' });
}

export function formatConfidencePercent(confidence) {
  if (confidence === null || confidence === undefined || Number.isNaN(Number(confidence))) {
    return null;
  }
  let value = Number(confidence);
  if (value > 0 && value <= 1) value *= 100;
  value = Math.min(100, Math.max(0, value));
  return Math.round(value * 10) / 10;
}

export function confidenceLabel(percent) {
  if (percent === null) return '';
  if (percent >= 75) return 'High confidence';
  if (percent >= 45) return 'Moderate confidence';
  return 'Low confidence';
}
