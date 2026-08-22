import { useEffect, useRef } from 'react';
import Card from '../ui/Card.jsx';
import Spinner from '../ui/Spinner.jsx';
import { SendIcon } from '../icons.jsx';

const SUGGESTIONS = [
  'Maximum operating pressure',
  'Motor power',
  'Flow rate',
  'Product applications',
  'Warranty',
];

export default function QuestionInput({ value, onChange, onSubmit, loading, focusToken = 0 }) {
  const textareaRef = useRef(null);
  const canSubmit = Boolean(value.trim()) && !loading;

  useEffect(() => {
    if (focusToken > 0) textareaRef.current?.focus();
  }, [focusToken]);

  return (
    <Card
      className="question-card"
      title="Ask a question"
      subtitle="Answers are derived from the uploaded document and its evidence."
    >
      <form
        className="question-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (canSubmit) onSubmit();
        }}
      >
        <textarea
          ref={textareaRef}
          className="question-form__input"
          rows={3}
          value={value}
          placeholder="e.g. What is the maximum operating pressure?"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              if (canSubmit) onSubmit();
            }
          }}
          disabled={loading}
        />
        <div className="question-form__footer">
          <div className="question-form__suggestions">
            <p className="question-form__label">Suggested questions</p>
            <div className="question-form__chips">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="chip chip--action"
                  disabled={loading}
                  onClick={() => {
                    onChange(suggestion);
                    textareaRef.current?.focus();
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
          <button type="submit" className="btn btn--primary" disabled={!canSubmit}>
            {loading ? <Spinner size={14} /> : <SendIcon size={14} />}
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </div>
        <p className="question-form__hint">Press Enter to ask · Shift + Enter for a new line</p>
      </form>
    </Card>
  );
}
