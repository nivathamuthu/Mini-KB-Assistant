import { FormEvent, useState } from "react";

type Props = {
  onAsk: (question: string) => void;
  loading: boolean;
};

export default function AskForm({ onAsk, loading }: Props) {
  const [question, setQuestion] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    onAsk(trimmed);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      submit(e as unknown as FormEvent);
    }
  };

  return (
    <form onSubmit={submit} className="ask-form">
      <label htmlFor="question">Your question</label>
      <textarea
        id="question"
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="e.g. How long do I have to request a refund?"
        disabled={loading}
      />
      <button type="submit" disabled={loading || !question.trim()}>
        Ask
      </button>
      <p className="hint">Ctrl+Enter to submit</p>
    </form>
  );
}
