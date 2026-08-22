import Card from '../ui/Card.jsx';
import StatusPill from '../ui/StatusPill.jsx';
import Skeleton from '../ui/Skeleton.jsx';
import ErrorBanner from '../ui/ErrorBanner.jsx';
import EmptyState from '../ui/EmptyState.jsx';
import StructuredAnswer from './StructuredAnswer.jsx';
import { AlertTriangleIcon, ChatIcon, ExternalLinkIcon, InfoIcon } from '../icons.jsx';
import {
  QUERY_STATUS,
  describeQueryStatus,
  describeValidation,
} from '../../utils/status.js';

const NOTICE_ICONS = {
  warning: <AlertTriangleIcon size={18} />,
  info: <InfoIcon size={18} />,
  neutral: <InfoIcon size={18} />,
};

function Notice({ tone = 'neutral', title, message, children }) {
  return (
    <div className={`notice notice--${tone}`} role="status">
      <span className="notice__icon">{NOTICE_ICONS[tone] ?? NOTICE_ICONS.neutral}</span>
      <div>
        <p className="notice__title">{title}</p>
        {message && <p className="notice__message">{message}</p>}
        {children && <div className="notice__actions">{children}</div>}
      </div>
    </div>
  );
}

function hasAnswerContent(result) {
  if (!result?.answer) return false;
  const { answer } = result;
  return Boolean(
    answer.hasValue || (answer.text && answer.text.trim()) || answer.attribute,
  );
}

export default function AnswerCard({ query, onRetry, fileUrl }) {
  const { status, result, error } = query;

  let body;
  let headerPill;

  if (status === 'idle') {
    body = (
      <EmptyState
        className="empty-state--slim"
        icon={<ChatIcon size={22} />}
        title="No answer yet"
        description="Ask a question above and the answer, backed by evidence from the document, will appear here."
      />
    );
  } else if (status === 'loading') {
    headerPill = <StatusPill tone="primary">Analyzing…</StatusPill>;
    body = (
      <div className="answer-card__loading" aria-live="polite">
        <Skeleton className="skeleton--line" />
        <Skeleton className="skeleton--line" />
        <Skeleton className="skeleton--line skeleton--short" />
        <p className="answer-card__loading-label">Analyzing the document…</p>
      </div>
    );
  } else if (status === 'error') {
    headerPill = <StatusPill tone="danger">Failed</StatusPill>;
    body = (
      <ErrorBanner
        title="Could not answer the question"
        message={error}
        onRetry={onRetry}
        retryLabel="Retry"
      />
    );
  } else {
    const queryStatus = result?.status ?? null;
    const statusMeta = describeQueryStatus(queryStatus);
    const validation = describeValidation(result?.validationStatus);

    if (queryStatus === QUERY_STATUS.NO_EVIDENCE) {
      headerPill = <StatusPill tone="warning">No evidence</StatusPill>;
      body = (
        <Notice
          tone="warning"
          title="No sufficient evidence found in this document."
          message="The document does not contain enough relevant information to answer this question. Try rephrasing or asking about something else covered by the document."
        />
      );
    } else if (queryStatus === QUERY_STATUS.NO_ATTRIBUTE_FOUND) {
      headerPill = statusMeta ? <StatusPill tone={statusMeta.tone}>{statusMeta.label}</StatusPill> : undefined;
      body = (
        <Notice
          tone="neutral"
          title="No matching attribute found"
          message="This attribute does not appear to be mentioned in the document. Try asking about a different property."
        />
      );
    } else if (queryStatus === QUERY_STATUS.VISUAL_EVIDENCE_ONLY) {
      headerPill = statusMeta ? <StatusPill tone={statusMeta.tone}>{statusMeta.label}</StatusPill> : undefined;
      body = (
        <Notice
          tone="info"
          title="Visual document without readable text"
          message="The document contains visual content, but no readable text was detected in it, so text-based retrieval cannot answer questions about it."
        >
          {fileUrl && (
            <a className="btn btn--ghost btn--sm" href={fileUrl} target="_blank" rel="noreferrer">
              View uploaded file <ExternalLinkIcon size={14} />
            </a>
          )}
        </Notice>
      );
    } else {
      if (queryStatus === QUERY_STATUS.CONFLICT) {
        headerPill = <StatusPill tone="danger">Conflict</StatusPill>;
      } else if (queryStatus === QUERY_STATUS.VALIDATION_FAILED) {
        headerPill = <StatusPill tone="warning">Validation failed</StatusPill>;
      } else {
        headerPill = validation ? (
          <StatusPill tone={validation.tone}>{validation.label}</StatusPill>
        ) : (
          <StatusPill tone="success">Complete</StatusPill>
        );
      }

      body = (
        <>
          {queryStatus === QUERY_STATUS.CONFLICT && (
            <Notice
              tone="warning"
              title="Conflicting evidence detected"
              message="Different parts of the document provide conflicting values for this question. Review the supporting evidence below before relying on any single value."
            />
          )}
          {queryStatus === QUERY_STATUS.VALIDATION_FAILED && (
            <Notice
              tone="warning"
              title="Validation failed"
              message="A value was extracted from the document, but it could not be validated against the retrieved evidence. Treat it as unconfirmed."
            />
          )}

          {hasAnswerContent(result) ? (
            result.answer.kind === 'structured' ? (
              <div className="answer-card__structured">
                <StructuredAnswer
                  answer={result.answer}
                  validationStatus={result.validationStatus}
                  pages={result.pages}
                  evidenceCount={result.evidenceCount}
                />
              </div>
            ) : (
              <p className="answer-card__text">{result.answer.text}</p>
            )
          ) : (
            !['conflict', 'validation_failed'].includes(queryStatus) && (
              <Notice
                tone="neutral"
                title="Empty response"
                message="The backend returned an answer without content. Please try again."
              />
            )
          )}
        </>
      );
    }
  }

  return (
    <Card className="answer-card" title="Answer" actions={headerPill}>
      {body}
    </Card>
  );
}
