import { useState } from 'react';
import Card from '../ui/Card.jsx';
import Skeleton from '../ui/Skeleton.jsx';
import { ChevronDownIcon, FileTextIcon } from '../icons.jsx';
import { shouldShowEvidence } from '../../utils/status.js';
import { formatConfidencePercent } from '../../utils/format.js';

const STATUS_NOTES = {
  no_evidence: 'No evidence is available for this question.',
  no_attribute_found: 'No supporting passages were returned for this question.',
  visual_evidence_only: 'Evidence is unavailable because the document has no readable text.',
};

export default function EvidencePanel({ query }) {
  const [expandedIds, setExpandedIds] = useState({});
  const result = query.status === 'success' ? query.result : null;
  const evidence = result?.evidence ?? [];
  const canShowItems = shouldShowEvidence(result?.status);

  const toggle = (index) =>
    setExpandedIds((prev) => ({ ...prev, [index]: !prev[index] }));

  let body;
  if (query.status === 'loading') {
    body = (
      <div className="evidence-panel__loading">
        <Skeleton className="skeleton--line" />
        <Skeleton className="skeleton--line" />
      </div>
    );
  } else if (query.status !== 'success') {
    body = (
      <p className="evidence-panel__empty">
        Supporting passages will appear here after you ask a question.
      </p>
    );
  } else if (!canShowItems) {
    body = (
      <p className="evidence-panel__empty">
        {STATUS_NOTES[result?.status] ?? 'No evidence was returned for this question.'}
      </p>
    );
  } else if (evidence.length === 0) {
    body = <p className="evidence-panel__empty">No evidence was returned for this question.</p>;
  } else {
    body = (
      <ul className="evidence-list">
        {evidence.map((item, index) => {
          const isOpen = Boolean(expandedIds[index]);
          const snippet = item.text ? item.text.replace(/\s+/g, ' ').trim() : '';
          const similarity =
            item.similarity !== null ? formatConfidencePercent(item.similarity) : null;
          return (
            <li key={index} className={`evidence-item${isOpen ? ' evidence-item--open' : ''}`}>
              <button
                type="button"
                className="evidence-item__head"
                onClick={() => toggle(index)}
                aria-expanded={isOpen}
              >
                <span className="evidence-item__badge">
                  {item.page !== null ? `Page ${item.page}` : 'Source'}
                </span>
                <span className="evidence-item__snippet">{snippet || 'No excerpt provided'}</span>
                {similarity !== null && (
                  <span
                    className="evidence-item__match"
                    title="Retrieval similarity reported by the backend"
                  >
                    {similarity}%
                  </span>
                )}
                <ChevronDownIcon size={15} className="evidence-item__chevron" />
              </button>
              {isOpen && (
                <div className="evidence-item__body">
                  <p>{item.text || 'No excerpt was provided for this piece of evidence.'}</p>
                  {(item.source || similarity !== null) && (
                    <p className="evidence-item__source">
                      {item.source && (
                        <>
                          <FileTextIcon size={13} /> {item.source}
                        </>
                      )}
                      {similarity !== null && <span>Similarity: {similarity}%</span>}
                    </p>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <Card
      className="evidence-panel"
      title="Supporting evidence"
      subtitle="Passages retrieved from the document"
      actions={
        canShowItems && query.status === 'success' && evidence.length > 0 ? (
          <span className="count-pill">{evidence.length}</span>
        ) : undefined
      }
    >
      {body}
    </Card>
  );
}
