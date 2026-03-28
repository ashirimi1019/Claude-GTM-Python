/**
 * Backend proxy helpers for communicating with the Python FastAPI backend.
 *
 * All Next.js API routes delegate to the Python backend via these helpers,
 * keeping the frontend a thin proxy layer.
 */

const BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export function backendUrl(path: string): string {
  return `${BACKEND_URL}${path}`;
}

export async function proxyGet(path: string, init?: RequestInit): Promise<Response> {
  return fetch(backendUrl(path), { ...init, method: 'GET' });
}

export async function proxyPost(path: string, body?: unknown, init?: RequestInit): Promise<Response> {
  return fetch(backendUrl(path), {
    ...init,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    body: body ? JSON.stringify(body) : undefined,
  });
}
