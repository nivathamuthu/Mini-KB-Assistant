import { FormEvent, useEffect, useState } from "react";
import { DocumentListItem, HttpError, createDocument, listDocuments } from "../api";

export default function DocumentsPanel() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [items, setItems] = useState<DocumentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const limit = 10;

  const load = async (newOffset = offset) => {
    try {
      const data = await listDocuments(limit, newOffset);
      setItems(data.items);
      setTotal(data.total);
      setOffset(newOffset);
    } catch (err) {
      setMessage(err instanceof HttpError ? err.message : "Failed to load documents.");
    }
  };

  useEffect(() => {
    void load(0);
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await createDocument(title.trim(), content.trim());
      setTitle("");
      setContent("");
      setMessage("Document indexed.");
      await load(0);
    } catch (err) {
      setMessage(err instanceof HttpError ? err.message : "Failed to add document.");
    }
  };

  return (
    <section className="card documents-panel">
      <h2>Knowledge articles</h2>
      <form onSubmit={onSubmit} className="doc-form">
        <label htmlFor="doc-title">Title</label>
        <input
          id="doc-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <label htmlFor="doc-content">Content</label>
        <textarea
          id="doc-content"
          rows={5}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
        />
        <button type="submit">Add document</button>
      </form>
      {message && <p className="muted">{message}</p>}
      <ul className="doc-list">
        {items.map((d) => (
          <li key={d.document_id}>
            <strong>{d.title}</strong>
            <span>{new Date(d.created_at).toLocaleString()}</span>
          </li>
        ))}
      </ul>
      <div className="pager">
        <button type="button" disabled={offset === 0} onClick={() => void load(Math.max(0, offset - limit))}>
          Previous
        </button>
        <span>
          {offset + 1}–{Math.min(offset + limit, total)} of {total}
        </span>
        <button
          type="button"
          disabled={offset + limit >= total}
          onClick={() => void load(offset + limit)}
        >
          Next
        </button>
      </div>
    </section>
  );
}
