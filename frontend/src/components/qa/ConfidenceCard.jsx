import Card from '../ui/Card.jsx';
import Skeleton from '../ui/Skeleton.jsx';
import StatusPill from '../ui/StatusPill.jsx';
import { confidenceLabel, formatConfidencePercent } from '../../utils/format.js';
import { describeValidation } from '../../utils/status.js';

export default function ConfidenceCard({ query }) {
  const percent = query.result ? formatConfidencePercent(query.result.confidence) : null;
  const validation = query.result ? describeValidation(query.result.validationStatus) : null;

  let body;
  if (query.status === 'loading') {
    body = (
      <div className="confidence-card__loading">
        <Skeleton className="confidence-card__value-skeleton" />
        <Skeleton className="skeleton--line" />
      </div>
    );
  } else if (query.status === 'success' && percent !== null) {
    body = (
      <>
        <p className="confidence-card__value">
          {percent}
          <span>%</span>
        </p>
        <div className="confidence-card__bar">
          <div
            className="confidence-card__bar-fill"
            style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
          />
        </div>
        <p className="confidence-card__label">{confidenceLabel(percent)}</p>
        {validation && <StatusPill tone={validation.tone}>{validation.label}</StatusPill>}
      </>
    );
  } else if (query.status === 'success') {
    body = (
      <p className="confidence-card__empty">
        The backend did not return a confidence score for this answer.
      </p>
    );
  } else if (query.status === 'error') {
    body = (
      <p className="confidence-card__empty">Confidence is unavailable because the query failed.</p>
    );
  } else {
    body = (
      <>
        <p className="confidence-card__value confidence-card__value--idle">—</p>
        <p className="confidence-card__empty">Ask a question to see the reported confidence.</p>
      </>
    );
  }

  return (
    <Card
      className="confidence-card"
      title="Confidence"
      subtitle="Reported by the analysis backend"
    >
      <div className="confidence-card__body">{body}</div>
    </Card>
  );
}
