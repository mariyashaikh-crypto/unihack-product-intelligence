const BASE_URL = 'http://127.0.0.1:8000';

export class ApiError extends Error {
  constructor(message, { status = 0, details = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

function extractErrorMessage(payload, status) {
  if (payload && typeof payload === 'object') {
    const detail = payload.detail ?? payload.message ?? payload.error;
    if (typeof detail === 'string' && detail.trim()) return detail;
    if (Array.isArray(detail)) {
      const first = detail.find((item) => item && typeof item.msg === 'string');
      if (first) return first.msg;
    } else if (detail && typeof detail.msg === 'string') {
      return detail.msg;
    }
  }
  if (typeof payload === 'string' && payload.trim()) return payload.trim();
  return `Request failed with status ${status}.`;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch {
    throw new ApiError(
      `Unable to reach the backend at ${BASE_URL}. Make sure the server is running.`,
    );
  }

  let payload = null;
  const rawBody = await response.text();
  if (rawBody) {
    try {
      payload = JSON.parse(rawBody);
    } catch {
      payload = rawBody;
    }
  }

  if (!response.ok) {
    throw new ApiError(extractErrorMessage(payload, response.status), {
      status: response.status,
      details: payload && typeof payload === 'object' ? payload : null,
    });
  }

  return payload;
}

function pickDocumentId(payload) {
  if (!payload || typeof payload !== 'object') return null;
  return payload.document_id ?? payload.id ?? payload.uuid ?? payload.file_id ?? null;
}

function toNullableNumber(value) {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

export function resolveFileUrl(url) {
  if (!url || typeof url !== 'string') return null;
  if (/^https?:\/\//i.test(url)) return url;
  return `${BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;
}

function normalizePages(value) {
  if (value === null || value === undefined) return [];
  const list = Array.isArray(value) ? value : [value];
  return list.map(toNullableNumber).filter((page) => page !== null);
}

export function normalizeDocument(payload, forcedId = null) {
  const raw = payload && typeof payload === 'object' ? payload : {};
  const id = forcedId ?? pickDocumentId(raw);
  return {
    id,
    filename: raw.filename ?? raw.file_name ?? raw.name ?? 'Untitled document',
    contentType: raw.content_type ?? raw.mime_type ?? raw.type ?? null,
    size: toNullableNumber(raw.size ?? raw.file_size),
    uploadedAt: raw.uploaded_at ?? raw.created_at ?? raw.timestamp ?? null,
    pages: toNullableNumber(raw.pages),
    chunks: toNullableNumber(raw.chunks),
    visualOnly: typeof raw.visual_only === 'boolean' ? raw.visual_only : null,
    fileUrl:
      resolveFileUrl(raw.file_url) ?? (id ? getDocumentFileUrl(id) : null),
    raw,
  };
}

function mapEvidenceItem(item) {
  if (typeof item === 'string') {
    return { page: null, text: item, source: null, similarity: null };
  }
  const source = item && typeof item === 'object' ? item : {};
  return {
    page: toNullableNumber(source.page ?? source.page_number ?? source.page_num),
    text: source.text ?? source.excerpt ?? source.content ?? source.snippet ?? source.chunk ?? '',
    source: source.source ?? source.document ?? source.file ?? null,
    similarity: toNullableNumber(source.similarity ?? source.similarity_score ?? source.score),
  };
}

export function normalizeQueryResult(payload) {
  const raw = payload && typeof payload === 'object' ? payload : {};

  const answerRaw = raw.answer ?? raw.response ?? null;

  let answer = null;
  let validationStatus = raw.validation_status ?? raw.validation ?? null;
  let nestedConfidence = null;
  let nestedEvidence = [];
  let pages = [];
  let evidenceCount = null;

  if (answerRaw && typeof answerRaw === 'object') {
    answer = {
      kind: 'structured',
      attribute: typeof answerRaw.attribute === 'string' ? answerRaw.attribute : null,
      value: answerRaw.value ?? null,
      hasValue: answerRaw.value !== null && answerRaw.value !== undefined,
      unit: typeof answerRaw.unit === 'string' ? answerRaw.unit : null,
      text: typeof answerRaw.text === 'string' ? answerRaw.text : null,
    };
    validationStatus =
      (typeof answerRaw.status === 'string' ? answerRaw.status : null) ?? validationStatus;
    pages = normalizePages(answerRaw.pages);
    evidenceCount = toNullableNumber(answerRaw.evidence_count);
    nestedConfidence = toNullableNumber(answerRaw.confidence);
    nestedEvidence = Array.isArray(answerRaw.evidence) ? answerRaw.evidence : [];
  } else if (answerRaw !== null && answerRaw !== undefined) {
    answer = { kind: 'text', text: String(answerRaw) };
  }

  const evidenceSource =
    [raw.evidence, nestedEvidence, raw.sources, raw.citations, raw.passages].find((candidate) =>
      Array.isArray(candidate),
    ) ?? [];

  return {
    status: typeof raw.status === 'string' ? raw.status : null,
    question: typeof raw.question === 'string' ? raw.question : null,
    answer,
    confidence: toNullableNumber(raw.confidence) ?? nestedConfidence,
    validationStatus,
    pages,
    evidenceCount,
    evidence: evidenceSource.map(mapEvidenceItem),
    raw,
  };
}

export function checkHealth() {
  return request('/health');
}

export function getDocumentFileUrl(documentId) {
  return `${BASE_URL}/documents/${encodeURIComponent(documentId)}/file`;
}

export async function listDocuments() {
  const payload = await request('/documents');
  const candidates = Array.isArray(payload)
    ? payload
    : payload && typeof payload === 'object'
      ? (payload.documents ?? payload.items ?? payload.data)
      : null;

  if (!Array.isArray(candidates)) {
    throw new ApiError('The backend returned an unexpected response for GET /documents.');
  }

  return candidates.map((entry) => normalizeDocument(entry));
}

export async function queryDocument({ documentId, question, topK = 3 }) {
  if (!documentId) {
    throw new ApiError('No document is selected.');
  }

  const payload = await request('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      question,
      top_k: topK,
    }),
  });

  return normalizeQueryResult(payload);
}

export function uploadDocument(file, { onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE_URL}/upload`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && typeof onProgress === 'function') {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let payload = null;
      if (xhr.responseText) {
        try {
          payload = JSON.parse(xhr.responseText);
        } catch {
          payload = xhr.responseText;
        }
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        const documentId = pickDocumentId(payload);
        if (!documentId) {
          reject(
            new ApiError('The upload succeeded but the backend did not return a document id.', {
              status: xhr.status,
            }),
          );
          return;
        }
        resolve(normalizeDocument(payload, documentId));
        return;
      }

      reject(new ApiError(extractErrorMessage(payload, xhr.status), { status: xhr.status }));
    };

    xhr.onerror = () =>
      reject(
        new ApiError(`Unable to reach the backend at ${BASE_URL}. Make sure the server is running.`),
      );

    xhr.onabort = () => reject(new ApiError('The upload was cancelled.'));

    const formData = new FormData();
    formData.append('file', file);
    xhr.send(formData);
  });
}
