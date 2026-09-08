import Constants from "expo-constants";

type ExpoExtra = {
  apiBaseUrl?: string;
};

const extra = (Constants.expoConfig?.extra ?? {}) as ExpoExtra;

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_LYMEWIRE_API_URL ??
  extra.apiBaseUrl ??
  "https://lyme-ai-production.up.railway.app";

export type WireId = "ask" | "care" | "research" | "treatment" | "guideline" | "compare" | "trial" | "doctorbrief" | "calm";

export type WireAction = {
  id: WireId;
  title: string;
  subtitle: string;
  prompt: string;
};

export const WIRE_ACTIONS: WireAction[] = [
  {
    id: "care",
    title: "Care Wire",
    subtitle: "Doctor, center and treatment-route navigation",
    prompt: "Create a safe care route for Lyme or PTLDS symptoms.",
  },
  {
    id: "research",
    title: "Research Wire",
    subtitle: "PubMed-style evidence summaries",
    prompt: "Research PTLDS evidence and separate RCTs, reviews and uncertainty.",
  },
  {
    id: "treatment",
    title: "Treatment Wire",
    subtitle: "Benefit, risk and uncertainty checks",
    prompt: "Review this Lyme treatment claim with evidence and caveats.",
  },
  {
    id: "guideline",
    title: "Guideline Wire",
    subtitle: "CDC, NICE, IDSA and ILADS comparisons",
    prompt: "Compare Lyme guideline positions without false certainty.",
  },
  {
    id: "trial",
    title: "Trial Wire",
    subtitle: "ClinicalTrials.gov status snapshots",
    prompt: "Find active Lyme or PTLDS trials and explain what they test.",
  },
  {
    id: "doctorbrief",
    title: "Doctor Brief Wire",
    subtitle: "Clinician-ready visit summary",
    prompt: "Prepare a concise doctor brief from this symptom timeline.",
  },
  {
    id: "calm",
    title: "Calm Wire",
    subtitle: "Low-alarm support in panic moments",
    prompt: "Help me calm down and screen urgent red flags gently.",
  },
];
