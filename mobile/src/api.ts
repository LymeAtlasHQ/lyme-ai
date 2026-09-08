import { API_BASE_URL } from "./config";
import type { WireId } from "./config";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AskResponse = {
  brand?: string;
  wire?: string;
  answer?: string;
  retrieval_notes?: string[];
};

export async function askLymeWire(
  question: string,
  wire: WireId = "ask",
  history: ChatMessage[] = [],
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, wire, history }),
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
