import { useState } from "react";
import { SourceItem } from "../api";

type Props = {
  sources: SourceItem[];
};

function relevanceLabel(score: number): { text: string; className: string } {
  const pct = Math.round(score * 100);
  if (pct >= 70) return { text: `${pct}% match · Strong`, className: "relevance-high" };
  if (pct >= 40) return { text: `${pct}% match · Good`, className: "relevance-mid" };
  return { text: `${pct}% match · Related`, className: "relevance-low" };
}

function shortId(id: string): string {
  if (id.length <= 12) return id;
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

function SourceCard({ source, rank }: { source: SourceItem; rank: number }) {
  const [copied, setCopied] = useState(false);
  const relevance = relevanceLabel(source.score);

  const copyExcerpt = async () => {
    try {
      await navigator.clipboard.writeText(source.snippet);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <li className="source-card">
      <div className="source-card-header">
        <span className="source-rank" aria-hidden="true">
          #{rank}
        </span>
        <div className="source-meta">
          <h3 className="source-title">{source.title}</h3>
          <p className="source-submeta">
            <span className={`relevance-pill ${relevance.className}`}>{relevance.text}</span>
            <span className="source-divider" aria-hidden="true">
              ·
            </span>
            <span title={`Chunk index ${source.chunk_index} in this document`}>
              Part {source.chunk_index + 1}
            </span>
            <span className="source-divider" aria-hidden="true">
              ·
            </span>
            <span className="source-id" title={`Document ID: ${source.document_id}`}>
              ID {shortId(source.document_id)}
            </span>
          </p>
        </div>
      </div>

      <div className="source-excerpt-block">
        <div className="source-excerpt-label">
          <span>Exact excerpt used</span>
          <button type="button" className="btn-ghost" onClick={() => void copyExcerpt()}>
            {copied ? "Copied" : "Copy text"}
          </button>
        </div>
        <blockquote className="source-excerpt" cite={source.document_id}>
          {source.snippet}
        </blockquote>
      </div>
    </li>
  );
}

export default function SourceList({ sources }: Props) {
  if (!sources.length) {
    return (
      <div className="sources sources-empty">
        <h2 className="section-heading">Sources</h2>
        <div className="empty-sources-callout">
          <p className="empty-sources-title">No matching articles found</p>
          <p className="muted">
            The assistant could not tie this answer to any indexed document. Try rephrasing your
            question, or add a knowledge article below that covers this topic.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="sources">
      <div className="sources-intro">
        <h2 className="section-heading">Sources</h2>
        <p className="muted sources-help">
          {sources.length === 1
            ? "1 article excerpt was used to build the answer above."
            : `${sources.length} article excerpts were used (most relevant first).`}
        </p>
      </div>
      <ol className="source-list">
        {sources.map((s, index) => (
          <SourceCard key={`${s.document_id}-${s.chunk_index}`} source={s} rank={index + 1} />
        ))}
      </ol>
    </div>
  );
}
