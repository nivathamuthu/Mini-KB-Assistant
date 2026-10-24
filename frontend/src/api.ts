const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type SourceItem = {
  document_id: string;
  title: string;
  chunk_index: number;
  snippet: string;
  score: number;
};

export type AskResponse = {
  answer: string;
  sources: SourceItem[];
  mode: string;
};

export type DocumentListItem = {
  document_id: string;
  title: string;
  created_at: string;
};

export type DocumentListResponse = {
  items: DocumentListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
};

export class HttpError extends Error {
  status: number;
  code: string;
  requestId: string;
  retryAfter?: number;

  constructor(status: number, body: ApiError, retryAfter?: number) {
    super(body.error.message);
    this.status = status;
    this.code = body.error.code;
    this.requestId = body.error.request_id;
    this.retryAfter = retryAfter;
  }
}

async function parseJson<T>(resp: Response): Promise<T> {
  const text = await resp.text();
  if (!text) {
    throw new Error("Empty response from server.");
  }
  return JSON.parse(text) as T;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const resp = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!resp.ok) {
    const body = await parseJson<ApiError>(resp);
    const retryAfter = resp.headers.get("Retry-After");
    throw new HttpError(
      resp.status,
      body,
      retryAfter ? parseInt(retryAfter, 10) : undefined,
    );
  }
  return parseJson<AskResponse>(resp);
}

export async function createDocument(title: string, content: string) {
  const resp = await fetch(`${API_URL}/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content }),
  });
  if (!resp.ok) {
    const body = await parseJson<ApiError>(resp);
    throw new HttpError(resp.status, body);
  }
  return parseJson<{ document_id: string; chunk_count: number }>(resp);
}

export async function listDocuments(limit = 20, offset = 0): Promise<DocumentListResponse> {
  const resp = await fetch(`${API_URL}/documents?limit=${limit}&offset=${offset}`);
  if (!resp.ok) {
    const body = await parseJson<ApiError>(resp);
    throw new HttpError(resp.status, body);
  }
  return parseJson<DocumentListResponse>(resp);
}
