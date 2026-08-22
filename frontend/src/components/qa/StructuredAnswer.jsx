import StatusPill from '../ui/StatusPill.jsx';
import { describeValidation } from '../../utils/status.js';

function humanizeAttribute(attribute) {
  return attribute
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(value) {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : String(Math.round(value * 10000) / 10000);
  }
  return String(value);
}

export default function StructuredAnswer({ answer, validationStatus, pages, evidenceCount }) {
  const validation = describeValidation(validationStatus);
  const valueText = answer.hasValue ? formatValue(answer.value) : answer.text || null;

  return (
    <div className="structured-answer">
      <div className="structured-answer__main">
        <div className="structured-answer__reading">
          {answer.attribute && (
            <p className="structured-answer__attribute">{humanizeAttribute(answer.attribute)}</p>
          )}
          <p className="structured-answer__value">
            {valueText ?? '—'}
            {answer.unit && <span className="structured-answer__unit">{answer.unit}</span>}
          </p>
        </div>
        {validation && <StatusPill tone={validation.tone}>{validation.label}</StatusPill>}
      </div>

      {(pages.length > 0 || evidenceCount !== null) && (
        <div className="structured-answer__meta">
          {pages.length > 0 && (
            <span className="structured-answer__meta-group">
              <span className="structured-answer__meta-label">Source pages</span>
              <span className="structured-answer__page-chips">
                {pages.map((page) => (
                  <span key={page} className="chip">
                    Page {page}
                  </span>
                ))}
              </span>
            </span>
          )}
          {evidenceCount !== null && (
            <span className="structured-answer__meta-group">
              <span className="structured-answer__meta-label">Evidence</span>
              <span>
                {evidenceCount} supporting passage{evidenceCount === 1 ? '' : 's'}
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
