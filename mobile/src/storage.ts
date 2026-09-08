import AsyncStorage from "@react-native-async-storage/async-storage";

export type TimelineDraft = {
  symptoms: string;
  tests: string;
  treatments: string;
  questions: string;
};

const TIMELINE_KEY = "lymewire.timeline.v1";

export async function loadTimeline(): Promise<TimelineDraft> {
  const raw = await AsyncStorage.getItem(TIMELINE_KEY);
  if (!raw) {
    return {
      symptoms: "",
      tests: "",
      treatments: "",
      questions: "",
    };
  }

  return JSON.parse(raw) as TimelineDraft;
}

export async function saveTimeline(timeline: TimelineDraft): Promise<void> {
  await AsyncStorage.setItem(TIMELINE_KEY, JSON.stringify(timeline));
}

export function buildBriefFromTimeline(timeline: TimelineDraft): string {
  return [
    "LymeWire doctor brief draft",
    "",
    `Main symptoms: ${timeline.symptoms || "Not entered yet."}`,
    `Tests / objective findings: ${timeline.tests || "Not entered yet."}`,
    `Treatments tried: ${timeline.treatments || "Not entered yet."}`,
    `Questions for clinician: ${timeline.questions || "Not entered yet."}`,
    "",
    "Please reassess active Lyme/tick-borne infection, PTLDS/persistent symptoms, coinfections, inflammatory/autoimmune causes, neurologic causes, medication effects, and other plausible explanations.",
  ].join("\n");
}
