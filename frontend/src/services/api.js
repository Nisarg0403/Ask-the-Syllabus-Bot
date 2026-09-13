const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export const OPENROUTER_MODELS = [
  "meta-llama/llama-3-8b-instruct:free",
  "mistralai/mistral-7b-instruct:free",
  "qwen/qwen-2.5-7b-instruct:free",
  "google/gemini-flash-1.5",
  "anthropic/claude-3.5-sonnet"
];

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) throw new Error("Failed to fetch models");
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function fetchDbStatus() {
  const res = await fetch(`${API_BASE}/api/status`);
  if (!res.ok) throw new Error("Failed to fetch DB status");
  return res.json();
}

export async function uploadDocument(file, chunkSize, chunkOverlap) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("chunk_size", chunkSize);
  formData.append("chunk_overlap", chunkOverlap);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail || "Upload failed");
  }

  return res.json();
}

export async function deleteDocument(filename) {
  const res = await fetch(`${API_BASE}/api/documents/${filename}`, {
    method: "DELETE"
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Delete failed");
  }

  return res.json();
}

export async function resetDatabase() {
  const res = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
  if (!res.ok) throw new Error("Reset failed");
  return res.json();
}

export async function querySyllabus(payload) {
  return fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function fetchEvaluationResults() {
  const res = await fetch(`${API_BASE}/api/evaluation/results`);
  if (!res.ok) throw new Error("Failed to fetch evaluation results");
  return res.json();
}
