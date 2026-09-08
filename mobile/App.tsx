import "react-native-url-polyfill/auto";

import { Ionicons } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import { askLymeWire, getHealth } from "./src/api";
import type { ChatMessage } from "./src/api";
import { API_BASE_URL, WIRE_ACTIONS } from "./src/config";
import type { WireAction, WireId } from "./src/config";
import { buildBriefFromTimeline, loadTimeline, saveTimeline, TimelineDraft } from "./src/storage";
import { colors, spacing } from "./src/theme";

type Message = {
  role: "user" | "assistant";
  text: string;
};

const Tab = createBottomTabNavigator();

const starterMessages: Message[] = [
  {
    role: "assistant",
    text:
      "LymeWire is active. Ask about Lyme, PTLDS, tick-borne illness evidence, care routes, guidelines, trials or doctor-brief prep.",
  },
];

function ScreenShell({ children }: { children: ReactNode }) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      {children}
    </SafeAreaView>
  );
}

function Header({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <View style={styles.header}>
      <Text style={styles.brand}>LymeWire</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
}

function toApiHistory(messages: Message[]): ChatMessage[] {
  return messages.slice(-10).map((message) => ({
    role: message.role,
    content: message.text,
  }));
}

function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>(starterMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    getHealth().then(setApiOnline);
  }, []);

  async function send(text: string = input, wire: WireId = "ask") {
    const question = text.trim();
    if (!question || loading) {
      return;
    }

    setInput("");
    setMessages((current) => [...current, { role: "user", text: question }]);
    setLoading(true);

    try {
      const answer = await askLymeWire(question, wire, toApiHistory(messages));
      setMessages((current) => [...current, { role: "assistant", text: answer }]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text:
            "I could not reach the LymeWire API. Check the Railway service or set EXPO_PUBLIC_LYMEWIRE_API_URL to the right backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScreenShell>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.flex}
      >
        <Header
          title="Find the signal"
          subtitle={apiOnline === false ? "API offline or unreachable" : "Evidence-aware Lyme navigation"}
        />
        <ScrollView style={styles.chatList} contentContainerStyle={styles.chatContent}>
          {messages.map((message, index) => (
            <View
              key={`${message.role}-${index}`}
              style={[styles.bubble, message.role === "user" ? styles.userBubble : styles.assistantBubble]}
            >
              <Text style={message.role === "user" ? styles.userText : styles.assistantText}>
                {message.text}
              </Text>
            </View>
          ))}
          {loading ? <ActivityIndicator color={colors.graphite} style={styles.loader} /> : null}
        </ScrollView>
        <View style={styles.quickRow}>
          {[
            { label: "Care route", wire: "care" as WireId },
            { label: "Research PTLDS", wire: "research" as WireId },
            { label: "Calm mode", wire: "calm" as WireId },
          ].map((action) => (
            <Pressable key={action.label} style={styles.quickButton} onPress={() => send(action.label, action.wire)}>
              <Text style={styles.quickText}>{action.label}</Text>
            </Pressable>
          ))}
        </View>
        <View style={styles.inputRow}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Ask LymeWire..."
            placeholderTextColor={colors.muted}
            multiline
            style={styles.input}
          />
          <Pressable accessibilityLabel="Send" style={styles.sendButton} onPress={() => send()}>
            <Ionicons name="send" color={colors.graphite} size={20} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </ScreenShell>
  );
}

function WiresScreen() {
  const [wireAnswer, setWireAnswer] = useState("");
  const [loadingWire, setLoadingWire] = useState<string | null>(null);

  async function runWire(wire: WireAction) {
    setLoadingWire(wire.id);
    setWireAnswer("");
    try {
      const answer = await askLymeWire(wire.prompt, wire.id);
      setWireAnswer(answer);
    } catch {
      setWireAnswer("LymeWire API is unreachable from this device right now.");
    } finally {
      setLoadingWire(null);
    }
  }

  return (
    <ScreenShell>
      <Header title="Wires" subtitle="Focused paths for care, research and clinician prep" />
      <ScrollView contentContainerStyle={styles.content}>
        {WIRE_ACTIONS.map((wire) => (
          <Pressable key={wire.id} style={styles.card} onPress={() => runWire(wire)}>
            <Text style={styles.cardTitle}>{wire.title}</Text>
            <Text style={styles.cardBody}>{wire.subtitle}</Text>
            <Text style={styles.promptText}>{wire.prompt}</Text>
            {loadingWire === wire.id ? <ActivityIndicator color={colors.graphite} style={styles.inlineLoader} /> : null}
          </Pressable>
        ))}
        {wireAnswer ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Wire answer</Text>
            <Text style={styles.cardBody}>{wireAnswer}</Text>
          </View>
        ) : null}
      </ScrollView>
    </ScreenShell>
  );
}

function TimelineScreen() {
  const [timeline, setTimeline] = useState<TimelineDraft>({
    symptoms: "",
    tests: "",
    treatments: "",
    questions: "",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadTimeline().then(setTimeline);
  }, []);

  async function update(key: keyof TimelineDraft, value: string) {
    const next = { ...timeline, [key]: value };
    setTimeline(next);
    setSaved(false);
    await saveTimeline(next);
    setSaved(true);
  }

  return (
    <ScreenShell>
      <Header title="Timeline" subtitle="User-controlled local notes for the first MVP" />
      <ScrollView contentContainerStyle={styles.content}>
        <Field label="Dominant symptoms" value={timeline.symptoms} onChangeText={(value) => update("symptoms", value)} />
        <Field label="Tests and objective findings" value={timeline.tests} onChangeText={(value) => update("tests", value)} />
        <Field label="Treatments tried" value={timeline.treatments} onChangeText={(value) => update("treatments", value)} />
        <Field label="Questions for clinician" value={timeline.questions} onChangeText={(value) => update("questions", value)} />
        <Text style={styles.savedText}>{saved ? "Saved locally on this device." : "Notes stay local until saved."}</Text>
      </ScrollView>
    </ScreenShell>
  );
}

function Field({
  label,
  value,
  onChangeText,
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        multiline
        textAlignVertical="top"
        style={styles.textArea}
      />
    </View>
  );
}

function BriefScreen() {
  const [brief, setBrief] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadTimeline().then((timeline) => setBrief(buildBriefFromTimeline(timeline)));
  }, []);

  async function copyBrief() {
    await Clipboard.setStringAsync(brief);
    setCopied(true);
  }

  return (
    <ScreenShell>
      <Header title="Doctor Brief" subtitle="A concise visit summary generated from local timeline notes" />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.mono}>{brief}</Text>
        </View>
        <Pressable style={styles.primaryButton} onPress={copyBrief}>
          <Text style={styles.primaryButtonText}>{copied ? "Copied" : "Copy brief"}</Text>
        </Pressable>
      </ScrollView>
    </ScreenShell>
  );
}

function SourcesScreen() {
  const sources = useMemo(
    () => [
      "CDC Lyme clinical care",
      "CDC chronic symptoms / PTLDS terminology",
      "IDSA/AAN/ACR Lyme guideline",
      "NICE NG95 Lyme disease",
      "PubMed evidence cards",
      "ClinicalTrials.gov trial cards",
    ],
    [],
  );

  return (
    <ScreenShell>
      <Header title="Sources" subtitle="Evidence types should stay labeled and traceable" />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Backend</Text>
          <Text style={styles.cardBody}>{API_BASE_URL}</Text>
        </View>
        {sources.map((source) => (
          <View key={source} style={styles.sourceRow}>
            <Ionicons name="checkmark-circle" color={colors.graphite} size={20} />
            <Text style={styles.sourceText}>{source}</Text>
          </View>
        ))}
        <Text style={styles.note}>
          This MVP labels sources and care boundaries. It does not store medical records, diagnose, prescribe or rank doctors by unverifiable success rates.
        </Text>
      </ScrollView>
    </ScreenShell>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarActiveTintColor: colors.graphite,
          tabBarInactiveTintColor: colors.muted,
          tabBarStyle: styles.tabBar,
          tabBarIcon: ({ color, size }) => {
            const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
              Chat: "chatbubble-ellipses",
              Wires: "git-network",
              Timeline: "pulse",
              Brief: "document-text",
              Sources: "library",
            };
            return <Ionicons name={icons[route.name]} color={color} size={size} />;
          },
        })}
      >
        <Tab.Screen name="Chat" component={ChatScreen} />
        <Tab.Screen name="Wires" component={WiresScreen} />
        <Tab.Screen name="Timeline" component={TimelineScreen} />
        <Tab.Screen name="Brief" component={BriefScreen} />
        <Tab.Screen name="Sources" component={SourcesScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
    backgroundColor: colors.background,
  },
  brand: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 0,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontSize: 31,
    fontWeight: "800",
    letterSpacing: 0,
    marginTop: spacing.xs,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 21,
    marginTop: spacing.xs,
  },
  chatList: {
    flex: 1,
  },
  chatContent: {
    padding: spacing.md,
    gap: spacing.sm,
  },
  bubble: {
    borderRadius: 8,
    padding: spacing.md,
    maxWidth: "92%",
  },
  assistantBubble: {
    alignSelf: "flex-start",
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderWidth: 1,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: colors.graphite,
  },
  assistantText: {
    color: colors.ink,
    fontSize: 16,
    lineHeight: 23,
  },
  userText: {
    color: colors.lime,
    fontSize: 16,
    lineHeight: 23,
  },
  loader: {
    alignSelf: "flex-start",
    marginVertical: spacing.sm,
  },
  inlineLoader: {
    alignSelf: "flex-start",
    marginTop: spacing.sm,
  },
  quickRow: {
    flexDirection: "row",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  quickButton: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  quickText: {
    color: colors.ink,
    fontWeight: "700",
  },
  inputRow: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: spacing.sm,
    padding: spacing.md,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    backgroundColor: colors.panel,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  sendButton: {
    alignItems: "center",
    backgroundColor: colors.lime,
    borderRadius: 8,
    height: 44,
    justifyContent: "center",
    width: 44,
  },
  content: {
    padding: spacing.md,
    gap: spacing.md,
  },
  card: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
  },
  cardBody: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: spacing.xs,
  },
  promptText: {
    color: colors.ink,
    fontSize: 14,
    lineHeight: 20,
    marginTop: spacing.sm,
  },
  field: {
    gap: spacing.xs,
  },
  label: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "800",
  },
  textArea: {
    minHeight: 92,
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    padding: spacing.md,
  },
  savedText: {
    color: colors.muted,
    fontSize: 13,
  },
  mono: {
    color: colors.ink,
    fontFamily: Platform.select({ ios: "Menlo", android: "monospace", default: "monospace" }),
    fontSize: 14,
    lineHeight: 21,
  },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.graphite,
    borderRadius: 8,
    padding: spacing.md,
  },
  primaryButtonText: {
    color: colors.lime,
    fontSize: 16,
    fontWeight: "800",
  },
  sourceRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md,
  },
  sourceText: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
  note: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  tabBar: {
    backgroundColor: colors.panel,
    borderTopColor: colors.border,
  },
});
