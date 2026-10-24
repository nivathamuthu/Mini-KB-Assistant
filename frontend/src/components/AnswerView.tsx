type Props = {
  answer: string;
  mode: string;
};

function modeLabel(mode: string): string {
  if (mode === "mock") {
    return "Demo mode (offline mock — for local testing only)";
  }
  if (mode === "openai") {
    return "Live AI provider (OpenAI)";
  }
  if (mode === "gemini" || mode === "google") {
    return "Live AI provider (Google Gemini)";
  }
  if (mode === "local") {
    return "Local embeddings + mock LLM";
  }
  return mode;
}

export default function AnswerView({ answer, mode }: Props) {
  return (
    <div className="answer">
      <h2 className="section-heading">Answer</h2>
      <div className="answer-body">{answer}</div>
      <p className="mode-line">
        <span className="mode-badge">{modeLabel(mode)}</span>
      </p>
    </div>
  );
}
