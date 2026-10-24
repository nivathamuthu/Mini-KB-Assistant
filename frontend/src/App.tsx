import { useState } from "react";
import AskForm from "./components/AskForm";
import AnswerView from "./components/AnswerView";
import SourceList from "./components/SourceList";
import ErrorBanner from "./components/ErrorBanner";
import DocumentsPanel from "./components/DocumentsPanel";
import { AskResponse, HttpError, askQuestion } from "./api";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<HttpError | Error | null>(null);

  const handleAsk = async (question: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await askQuestion(question);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Request failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      <header>
        <h1>Mini Knowledge Assistant</h1>
        <p className="subtitle">
          Step 1: Add articles below · Step 2: Ask a question · Step 3: Review the answer and
          sources
        </p>
      </header>

      <main>
        <section className="card">
          <AskForm onAsk={handleAsk} loading={loading} />
          <div aria-live="polite" className="status-region">
            {loading && <p className="loading">Thinking…</p>}
          </div>
          <ErrorBanner error={error} />
          {result && (
            <>
              <AnswerView answer={result.answer} mode={result.mode} />
              <SourceList sources={result.sources} />
            </>
          )}
        </section>

        <DocumentsPanel />
      </main>
    </div>
  );
}
