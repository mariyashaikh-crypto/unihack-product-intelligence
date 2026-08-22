import Card from '../ui/Card.jsx';
import { ChatIcon, ShieldCheckIcon, UploadCloudIcon } from '../icons.jsx';

const STEPS = [
  {
    icon: <UploadCloudIcon size={17} />,
    title: '1 · Upload a document',
    description: 'Drag in a product sheet, specification or photo (PDF or image).',
  },
  {
    icon: <ChatIcon size={17} />,
    title: '2 · Ask a question',
    description: 'Ask anything about the uploaded document in plain language.',
  },
  {
    icon: <ShieldCheckIcon size={17} />,
    title: '3 · Review the evidence',
    description: 'Check the answer, its confidence and the supporting pages.',
  },
];

export default function OnboardingPanel() {
  return (
    <Card
      className="onboarding-panel"
      title="How it works"
      subtitle="Three steps from document to verified answer"
    >
      <ol className="onboarding-panel__steps">
        {STEPS.map((step) => (
          <li key={step.title} className="onboarding-step">
            <span className="onboarding-step__icon">{step.icon}</span>
            <span className="onboarding-step__text">
              <span className="onboarding-step__title">{step.title}</span>
              <span className="onboarding-step__description">{step.description}</span>
            </span>
          </li>
        ))}
      </ol>
    </Card>
  );
}
