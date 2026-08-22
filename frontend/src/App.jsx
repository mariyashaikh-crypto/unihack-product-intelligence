import { useCallback, useEffect, useState } from 'react';
import Sidebar from './components/layout/Sidebar.jsx';
import Header from './components/layout/Header.jsx';
import UploadCard from './components/upload/UploadCard.jsx';
import DocumentInfoCard from './components/document/DocumentInfoCard.jsx';
import QuestionInput from './components/qa/QuestionInput.jsx';
import AnswerCard from './components/qa/AnswerCard.jsx';
import ConfidenceCard from './components/qa/ConfidenceCard.jsx';
import EvidencePanel from './components/qa/EvidencePanel.jsx';
import OnboardingPanel from './components/dashboard/OnboardingPanel.jsx';
import { checkHealth, listDocuments, queryDocument, uploadDocument } from './api/client.js';
import { validateFile } from './utils/files.js';

const IDLE_UPLOAD = { status: 'idle', progress: 0, error: null };
const IDLE_QUERY = { status: 'idle', result: null, error: null };

export default function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [connection, setConnection] = useState('checking');
  const [documents, setDocuments] = useState({ status: 'loading', items: [], error: null });
  const [activeDoc, setActiveDoc] = useState(null);
  const [upload, setUpload] = useState(IDLE_UPLOAD);
  const [question, setQuestion] = useState('');
  const [query, setQuery] = useState(IDLE_QUERY);
  const [focusToken, setFocusToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    checkHealth()
      .then(() => {
        if (!cancelled) setConnection('online');
      })
      .catch(() => {
        if (!cancelled) setConnection('offline');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshDocuments = useCallback(async () => {
    setDocuments((prev) => ({
      ...prev,
      status: prev.items.length ? 'ready' : 'loading',
      error: null,
    }));
    try {
      const items = await listDocuments();
      setDocuments({ status: 'ready', items, error: null });
    } catch (error) {
      setDocuments((prev) => ({
        ...prev,
        status: prev.items.length ? 'ready' : 'error',
        error: error.message,
      }));
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const resetConversation = useCallback(() => {
    setQuestion('');
    setQuery(IDLE_QUERY);
  }, []);

  const handleSelectDocument = useCallback(
    (doc) => {
      setActiveDoc(doc);
      resetConversation();
      setUpload(IDLE_UPLOAD);
      setIsSidebarOpen(false);
      setFocusToken((token) => token + 1);
    },
    [resetConversation],
  );

  const handleNewDocument = useCallback(() => {
    setActiveDoc(null);
    resetConversation();
    setUpload(IDLE_UPLOAD);
  }, [resetConversation]);

  const handleFileSelected = useCallback(
    async (file) => {
      const validation = validateFile(file);
      if (!validation.ok) {
        setUpload({ status: 'error', progress: 0, error: validation.error });
        return;
      }
      setUpload({ status: 'uploading', progress: 0, error: null });
      try {
        const doc = await uploadDocument(file, {
          onProgress: (progress) =>
            setUpload((prev) =>
              prev.status === 'uploading' ? { ...prev, progress } : prev,
            ),
        });
        setActiveDoc(doc);
        resetConversation();
        setUpload({ status: 'success', progress: 100, error: null });
        refreshDocuments();
        setFocusToken((token) => token + 1);
      } catch (error) {
        setUpload({ status: 'error', progress: 0, error: error.message });
      }
    },
    [refreshDocuments, resetConversation],
  );

  const handleAsk = useCallback(async () => {
    if (!activeDoc?.id) return;
    const trimmed = question.trim();
    if (!trimmed || query.status === 'loading') return;
    setQuery({ status: 'loading', result: null, error: null });
    try {
      const result = await queryDocument({
        documentId: activeDoc.id,
        question: trimmed,
        topK: 3,
      });
      setQuery({ status: 'success', result, error: null });
    } catch (error) {
      setQuery({ status: 'error', result: null, error: error.message });
    }
  }, [activeDoc, question, query.status]);

  return (
    <div className="app-shell">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        documents={documents}
        activeDocumentId={activeDoc?.id ?? null}
        onSelectDocument={handleSelectDocument}
        onRetryLoad={refreshDocuments}
        connection={connection}
      />
      <div className="app-main">
        <Header
          onMenuClick={() => setIsSidebarOpen(true)}
          connection={connection}
          hasActiveDoc={Boolean(activeDoc)}
          onNewDocument={handleNewDocument}
        />
        <main className="dashboard">
          {!activeDoc ? (
            <div className="dashboard__empty-layout">
              <UploadCard variant="hero" upload={upload} onFileSelected={handleFileSelected} />
              <OnboardingPanel />
            </div>
          ) : (
            <div className="dashboard__grid">
              <div className="dashboard__col-docs">
                <UploadCard
                  variant="compact"
                  upload={upload}
                  onFileSelected={handleFileSelected}
                />
                <DocumentInfoCard
                  doc={activeDoc}
                  onReplace={handleFileSelected}
                  onNewDocument={handleNewDocument}
                />
              </div>
              <div className="dashboard__col-qa">
                <QuestionInput
                  value={question}
                  onChange={setQuestion}
                  onSubmit={handleAsk}
                  loading={query.status === 'loading'}
                  focusToken={focusToken}
                />
                <AnswerCard
                  query={query}
                  onRetry={handleAsk}
                  fileUrl={activeDoc.fileUrl ?? null}
                />
                <div className="dashboard__qa-meta">
                  <ConfidenceCard query={query} />
                  <EvidencePanel query={query} />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
