import { API_BASE_URL } from "./config";

export type AskResponse = {
  brand?: string;
  wire?: string;
  answer?: string;
};

export async function askLymeWire(question: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`LymeWire API returned ${response.status}`);
  }

  const payload = (await response.json()) as AskResponse;
  return payload.answer?.trim() || "LymeWire did not return an answer.";
}

export async function getHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
