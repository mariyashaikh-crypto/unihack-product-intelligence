export const QUERY_STATUS = {
  SUCCESS: 'success',
  NO_EVIDENCE: 'no_evidence',
  NO_ATTRIBUTE_FOUND: 'no_attribute_found',
  VALIDATION_FAILED: 'validation_failed',
  CONFLICT: 'conflict',
  VISUAL_EVIDENCE_ONLY: 'visual_evidence_only',
};

const VALIDATION_TONES = {
  validated: { tone: 'success', label: 'Validated' },
  valid: { tone: 'success', label: 'Validated' },
  passed: { tone: 'success', label: 'Validated' },
  verified: { tone: 'success', label: 'Verified' },
  unvalidated: { tone: 'warning', label: 'Unvalidated' },
  unverified: { tone: 'warning', label: 'Unverified' },
  pending: { tone: 'warning', label: 'Pending review' },
  needs_review: { tone: 'warning', label: 'Needs review' },
  failed: { tone: 'danger', label: 'Failed' },
  invalid: { tone: 'danger', label: 'Invalid' },
};

const QUERY_STATUS_META = {
  no_evidence: { tone: 'warning', label: 'No evidence' },
  no_attribute_found: { tone: 'neutral', label: 'Not found' },
  validation_failed: { tone: 'warning', label: 'Validation failed' },
  conflict: { tone: 'danger', label: 'Conflict' },
  visual_evidence_only: { tone: 'primary', label: 'Visual only' },
};

const HIDE_EVIDENCE_STATUSES = new Set([
  'no_evidence',
  'no_attribute_found',
  'visual_evidence_only',
]);

function normalizeStatusKey(status) {
  return typeof status === 'string' ? status.trim().toLowerCase() : null;
}

export function describeQueryStatus(status) {
  const key = normalizeStatusKey(status);
  if (!key) return null;
  return QUERY_STATUS_META[key] ?? null;
}

export function shouldShowEvidence(queryStatus) {
  const key = normalizeStatusKey(queryStatus);
  if (!key) return true;
  return !HIDE_EVIDENCE_STATUSES.has(key);
}

export function describeValidation(status) {
  const key = normalizeStatusKey(status);
  if (!key) return null;
  const known = VALIDATION_TONES[key];
  if (known) return known;
  return {
    tone: 'neutral',
    label: key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()),
  };
}
