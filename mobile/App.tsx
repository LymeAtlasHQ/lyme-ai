import "react-native-url-polyfill/auto";

import { Ionicons } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import { StatusBar } from "expo-status-bar";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
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
import {
  buildBriefFromTimeline,
  loadSettings,
  loadTimeline,
  saveSettings,
  saveTimeline,
  type AppLanguage,
  type AppSettings,
  type TimelineDraft,
} from "./src/storage";
import { colors, spacing } from "./src/theme";

type Message = {
  role: "user" | "assistant";
  text: string;
};

type Copy = {
  starter: string;
  loginTitle: string;
  loginSubtitle: string;
  emailLabel: string;
  emailPlaceholder: string;
  continueGuest: string;
  loginSoon: string;
  language: string;
  chatTitle: string;
  chatSubtitle: string;
  apiOffline: string;
  apiError: string;
  askPlaceholder: string;
  send: string;
  careRoute: string;
  researchPtdls: string;
  calmMode: string;
  wiresTitle: string;
  wiresSubtitle: string;
  wireAnswer: string;
  timelineTitle: string;
  timelineSubtitle: string;
  symptoms: string;
  tests: string;
  treatments: string;
  questions: string;
  saved: string;
  unsaved: string;
  briefTitle: string;
  briefSubtitle: string;
  copied: string;
  copyBrief: string;
  sourcesTitle: string;
  sourcesSubtitle: string;
  backend: string;
  note: string;
  tabs: Record<string, string>;
};

const copy: Record<AppLanguage, Copy> = {
  tr: {
    starter:
      "LymeWire aktif. Lyme, PTLDS, kene kaynakli enfeksiyon kanitlari, bakim rotasi, kilavuzlar, klinik calismalar veya doktor gorusmesi hazirligi icin sorabilirsin.",
    loginTitle: "LymeWire'a hos geldin",
    loginSubtitle:
      "Simdilik misafir moduyla devam edebilirsin. Hesap girisi, ileride guvenli timeline ve cihazlar arasi senkron icin hazirlandi.",
    emailLabel: "E-posta (opsiyonel)",
    emailPlaceholder: "ornek@mail.com",
    continueGuest: "Misafir olarak devam et",
    loginSoon: "Guvenli login sonraki surumde Firebase/Auth ile baglanacak.",
    language: "Dil",
    chatTitle: "Sinyali bul",
    chatSubtitle: "Kanit odakli Lyme navigasyonu",
    apiOffline: "API cevrimdisi veya ulasilamiyor",
    apiError:
      "LymeWire API'ye ulasamadim. Railway servisinin acik oldugunu veya EXPO_PUBLIC_LYMEWIRE_API_URL ayarini kontrol et.",
    askPlaceholder: "LymeWire'a sor...",
    send: "Gonder",
    careRoute: "Bakim rotasi",
    researchPtdls: "PTLDS arastir",
    calmMode: "Sakin mod",
    wiresTitle: "Wire'lar",
    wiresSubtitle: "Bakim, arastirma ve doktor hazirligi icin odakli yollar",
    wireAnswer: "Wire cevabi",
    timelineTitle: "Timeline",
    timelineSubtitle: "Ilk MVP icin cihazda kalan, kullanici kontrollu notlar",
    symptoms: "Baskin semptomlar",
    tests: "Testler ve objektif bulgular",
    treatments: "Denenen tedaviler",
    questions: "Doktora sorulacak sorular",
    saved: "Bu cihaza lokal kaydedildi.",
    unsaved: "Notlar kaydedilene kadar lokal taslakta kalir.",
    briefTitle: "Doktor Ozeti",
    briefSubtitle: "Timeline notlarindan kisa gorusme ozeti",
    copied: "Kopyalandi",
    copyBrief: "Ozeti kopyala",
    sourcesTitle: "Kaynaklar",
    sourcesSubtitle: "Kanit tipleri etiketli ve izlenebilir kalmali",
    backend: "Backend",
    note:
      "Bu MVP kaynaklari ve bakim sinirlarini etiketler. Tibbi kayit saklamaz, tani koymaz, recete yazmaz veya doktorlari dogrulanamayan basari oranlarina gore siralamaz.",
    tabs: {
      Chat: "Sohbet",
      Wires: "Wire",
      Timeline: "Timeline",
      Brief: "Ozet",
      Sources: "Kaynak",
    },
  },
  en: {
    starter:
      "LymeWire is active. Ask about Lyme, PTLDS, tick-borne illness evidence, care routes, guidelines, trials or doctor-brief prep.",
    loginTitle: "Welcome to LymeWire",
    loginSubtitle:
      "You can continue as a guest for now. Account login is prepared for secure timeline sync in a later build.",
    emailLabel: "Email (optional)",
    emailPlaceholder: "name@example.com",
    continueGuest: "Continue as guest",
    loginSoon: "Secure login will connect through Firebase/Auth in the next release.",
    language: "Language",
    chatTitle: "Find the signal",
    chatSubtitle: "Evidence-aware Lyme navigation",
    apiOffline: "API offline or unreachable",
    apiError:
      "I could not reach the LymeWire API. Check the Railway service or set EXPO_PUBLIC_LYMEWIRE_API_URL to the right backend.",
    askPlaceholder: "Ask LymeWire...",
    send: "Send",
    careRoute: "Care route",
    researchPtdls: "Research PTLDS",
    calmMode: "Calm mode",
    wiresTitle: "Wires",
    wiresSubtitle: "Focused paths for care, research and clinician prep",
    wireAnswer: "Wire answer",
    timelineTitle: "Timeline",
    timelineSubtitle: "User-controlled local notes for the first MVP",
    symptoms: "Dominant symptoms",
    tests: "Tests and objective findings",
    treatments: "Treatments tried",
    questions: "Questions for clinician",
    saved: "Saved locally on this device.",
    unsaved: "Notes stay local until saved.",
    briefTitle: "Doctor Brief",
    briefSubtitle: "A concise visit summary generated from local timeline notes",
    copied: "Copied",
    copyBrief: "Copy brief",
    sourcesTitle: "Sources",
    sourcesSubtitle: "Evidence types should stay labeled and traceable",
    backend: "Backend",
    note:
      "This MVP labels sources and care boundaries. It does not store medical records, diagnose, prescribe or rank doctors by unverifiable success rates.",
    tabs: {
      Chat: "Chat",
      Wires: "Wires",
      Timeline: "Timeline",
      Brief: "Brief",
      Sources: "Sources",
    },
  },
};

const trWires: Record<WireId, { title: string; subtitle: string; prompt: string }> = {
  ask: { title: "Soru", subtitle: "Genel LymeWire cevabi", prompt: "LymeWire'a soru sor." },
  care: {
    title: "Bakim Wire",
    subtitle: "Doktor, merkez ve tedavi rotasi navigasyonu",
    prompt: "Lyme veya PTLDS semptomlari icin guvenli bir bakim rotasi cikar.",
  },
  research: {
    title: "Arastirma Wire",
    subtitle: "PubMed tarzi kanit ozetleri",
    prompt: "PTLDS kanitlarini arastir; RCT, derleme ve belirsizlikleri ayir.",
  },
  treatment: {
    title: "Tedavi Wire",
    subtitle: "Fayda, risk ve belirsizlik kontrolu",
    prompt: "Bu Lyme tedavi iddiasini kanit ve uyarilarla degerlendir.",
  },
  guideline: {
    title: "Kilavuz Wire",
    subtitle: "CDC, NICE, IDSA ve ILADS karsilastirmalari",
    prompt: "Lyme kilavuz pozisyonlarini yalanci kesinlik kurmadan karsilastir.",
  },
  compare: {
    title: "Karsilastirma Wire",
    subtitle: "Yaklasimlari yanyana tartar",
    prompt: "Bu iki Lyme yaklasimini kanit, risk ve belirsizlikle karsilastir.",
  },
  trial: {
    title: "Klinik Calisma Wire",
    subtitle: "ClinicalTrials.gov durum ozetleri",
    prompt: "Aktif Lyme veya PTLDS calismalarini bul ve ne test ettiklerini acikla.",
  },
  doctorbrief: {
    title: "Doktor Ozeti Wire",
    subtitle: "Klinisyene hazir gorusme ozeti",
    prompt: "Bu semptom timeline'indan kisa bir doktor ozeti hazirla.",
  },
  calm: {
    title: "Sakin Wire",
    subtitle: "Panik anlarinda dusuk alarmli destek",
    prompt: "Sakinlesmeme yardim et ve acil kirmizi bayraklari nazikce tara.",
  },
};

const enWires: Record<WireId, { title: string; subtitle: string; prompt: string }> = {
  ask: { title: "Ask", subtitle: "General LymeWire answer", prompt: "Ask LymeWire a question." },
  care: WIRE_ACTIONS.find((wire) => wire.id === "care")!,
  research: WIRE_ACTIONS.find((wire) => wire.id === "research")!,
  treatment: WIRE_ACTIONS.find((wire) => wire.id === "treatment")!,
  guideline: WIRE_ACTIONS.find((wire) => wire.id === "guideline")!,
  compare: { title: "Compare Wire", subtitle: "Compare care approaches", prompt: "Compare these Lyme approaches with evidence, risks and uncertainty." },
  trial: WIRE_ACTIONS.find((wire) => wire.id === "trial")!,
  doctorbrief: WIRE_ACTIONS.find((wire) => wire.id === "doctorbrief")!,
  calm: WIRE_ACTIONS.find((wire) => wire.id === "calm")!,
};

const wireCopy: Record<AppLanguage, Record<WireId, { title: string; subtitle: string; prompt: string }>> = {
  tr: trWires,
  en: enWires,
};

type AppContextValue = {
  language: AppLanguage;
  t: Copy;
  setLanguage: (language: AppLanguage) => void;
};

const AppContext = createContext<AppContextValue | null>(null);
const Tab = createBottomTabNavigator();

function useAppCopy() {
  const value = useContext(AppContext);
  if (!value) {
    throw new Error("App context is missing");
  }
  return value;
}

function ScreenShell({ children }: { children: ReactNode }) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      {children}
    </SafeAreaView>
  );
}

function LanguageToggle() {
  const { language, setLanguage, t } = useAppCopy();
  return (
    <View style={styles.languageRow}>
      <Text style={styles.languageLabel}>{t.language}</Text>
      {(["tr", "en"] as AppLanguage[]).map((item) => (
        <Pressable
          key={item}
          onPress={() => setLanguage(item)}
          style={[styles.languageButton, language === item ? styles.languageButtonActive : null]}
        >
          <Text style={[styles.languageText, language === item ? styles.languageTextActive : null]}>
            {item.toUpperCase()}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

function Header({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <View style={styles.header}>
      <View style={styles.headerTop}>
        <Text style={styles.brand}>LymeWire</Text>
        <LanguageToggle />
      </View>
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

function LoginScreen({ onContinue }: { onContinue: (email?: string) => void }) {
  const { t } = useAppCopy();
  const [email, setEmail] = useState("");

  return (
    <ScreenShell>
      <View style={styles.login}>
        <Text style={styles.brand}>LymeWire</Text>
        <Text style={styles.loginTitle}>{t.loginTitle}</Text>
        <Text style={styles.subtitle}>{t.loginSubtitle}</Text>
        <LanguageToggle />
        <View style={styles.field}>
          <Text style={styles.label}>{t.emailLabel}</Text>
          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            onChangeText={setEmail}
            placeholder={t.emailPlaceholder}
            placeholderTextColor={colors.muted}
            style={styles.input}
            value={email}
          />
        </View>
        <Pressable style={styles.primaryButton} onPress={() => onContinue(email.trim() || undefined)}>
          <Text style={styles.primaryButtonText}>{t.continueGuest}</Text>
        </Pressable>
        <Text style={styles.note}>{t.loginSoon}</Text>
      </View>
    </ScreenShell>
  );
}

function ChatScreen() {
  const { language, t } = useAppCopy();
  const starterMessages = useMemo<Message[]>(() => [{ role: "assistant", text: t.starter }], [t.starter]);
  const [messages, setMessages] = useState<Message[]>(starterMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    setMessages(starterMessages);
  }, [starterMessages]);

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
      const answer = await askLymeWire(question, wire, toApiHistory(messages), language);
      setMessages((current) => [...current, { role: "assistant", text: answer }]);
    } catch {
      setMessages((current) => [...current, { role: "assistant", text: t.apiError }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScreenShell>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.flex}>
        <Header title={t.chatTitle} subtitle={apiOnline === false ? t.apiOffline : t.chatSubtitle} />
        <ScrollView style={styles.chatList} contentContainerStyle={styles.chatContent}>
          {messages.map((message, index) => (
            <View
              key={`${message.role}-${index}`}
              style={[styles.bubble, message.role === "user" ? styles.userBubble : styles.assistantBubble]}
            >
              <Text style={message.role === "user" ? styles.userText : styles.assistantText}>{message.text}</Text>
            </View>
          ))}
          {loading ? <ActivityIndicator color={colors.graphite} style={styles.loader} /> : null}
        </ScrollView>
        <View style={styles.quickRow}>
          {[
            { label: t.careRoute, wire: "care" as WireId },
            { label: t.researchPtdls, wire: "research" as WireId },
            { label: t.calmMode, wire: "calm" as WireId },
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
            placeholder={t.askPlaceholder}
            placeholderTextColor={colors.muted}
            multiline
            style={styles.input}
          />
          <Pressable accessibilityLabel={t.send} style={styles.sendButton} onPress={() => send()}>
            <Ionicons name="send" color={colors.graphite} size={20} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </ScreenShell>
  );
}

function WiresScreen() {
  const { language, t } = useAppCopy();
  const [wireAnswer, setWireAnswer] = useState("");
  const [loadingWire, setLoadingWire] = useState<string | null>(null);

  async function runWire(wire: WireAction) {
    const localWire = wireCopy[language][wire.id];
    setLoadingWire(wire.id);
    setWireAnswer("");
    try {
      const answer = await askLymeWire(localWire.prompt, wire.id, [], language);
      setWireAnswer(answer);
    } catch {
      setWireAnswer(t.apiError);
    } finally {
      setLoadingWire(null);
    }
  }

  return (
    <ScreenShell>
      <Header title={t.wiresTitle} subtitle={t.wiresSubtitle} />
      <ScrollView contentContainerStyle={styles.content}>
        {WIRE_ACTIONS.map((wire) => {
          const localWire = wireCopy[language][wire.id];
          return (
            <Pressable key={wire.id} style={styles.card} onPress={() => runWire(wire)}>
              <Text style={styles.cardTitle}>{localWire.title}</Text>
              <Text style={styles.cardBody}>{localWire.subtitle}</Text>
              <Text style={styles.promptText}>{localWire.prompt}</Text>
              {loadingWire === wire.id ? <ActivityIndicator color={colors.graphite} style={styles.inlineLoader} /> : null}
            </Pressable>
          );
        })}
        {wireAnswer ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{t.wireAnswer}</Text>
            <Text style={styles.cardBody}>{wireAnswer}</Text>
          </View>
        ) : null}
      </ScrollView>
    </ScreenShell>
  );
}

function TimelineScreen() {
  const { t } = useAppCopy();
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
      <Header title={t.timelineTitle} subtitle={t.timelineSubtitle} />
      <ScrollView contentContainerStyle={styles.content}>
        <Field label={t.symptoms} value={timeline.symptoms} onChangeText={(value) => update("symptoms", value)} />
        <Field label={t.tests} value={timeline.tests} onChangeText={(value) => update("tests", value)} />
        <Field label={t.treatments} value={timeline.treatments} onChangeText={(value) => update("treatments", value)} />
        <Field label={t.questions} value={timeline.questions} onChangeText={(value) => update("questions", value)} />
        <Text style={styles.savedText}>{saved ? t.saved : t.unsaved}</Text>
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
      <TextInput value={value} onChangeText={onChangeText} multiline textAlignVertical="top" style={styles.textArea} />
    </View>
  );
}

function BriefScreen() {
  const { t } = useAppCopy();
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
      <Header title={t.briefTitle} subtitle={t.briefSubtitle} />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.mono}>{brief}</Text>
        </View>
        <Pressable style={styles.primaryButton} onPress={copyBrief}>
          <Text style={styles.primaryButtonText}>{copied ? t.copied : t.copyBrief}</Text>
        </Pressable>
      </ScrollView>
    </ScreenShell>
  );
}

function SourcesScreen() {
  const { t } = useAppCopy();
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
      <Header title={t.sourcesTitle} subtitle={t.sourcesSubtitle} />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{t.backend}</Text>
          <Text style={styles.cardBody}>{API_BASE_URL}</Text>
        </View>
        {sources.map((source) => (
          <View key={source} style={styles.sourceRow}>
            <Ionicons name="checkmark-circle" color={colors.graphite} size={20} />
            <Text style={styles.sourceText}>{source}</Text>
          </View>
        ))}
        <Text style={styles.note}>{t.note}</Text>
      </ScrollView>
    </ScreenShell>
  );
}

function AppTabs() {
  const { t } = useAppCopy();
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarActiveTintColor: colors.graphite,
          tabBarInactiveTintColor: colors.muted,
          tabBarLabel: t.tabs[route.name],
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

export default function App() {
  const [settings, setSettings] = useState<AppSettings>({ language: "tr", onboarded: false });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadSettings().then((loaded) => {
      setSettings(loaded);
      setReady(true);
    });
  }, []);

  async function updateSettings(next: AppSettings) {
    setSettings(next);
    await saveSettings(next);
  }

  const contextValue = useMemo<AppContextValue>(
    () => ({
      language: settings.language,
      t: copy[settings.language],
      setLanguage: (language) => updateSettings({ ...settings, language }),
    }),
    [settings],
  );

  if (!ready) {
    return (
      <ScreenShell>
        <ActivityIndicator color={colors.graphite} style={styles.fullLoader} />
      </ScreenShell>
    );
  }

  return (
    <AppContext.Provider value={contextValue}>
      {settings.onboarded ? (
        <AppTabs />
      ) : (
        <LoginScreen onContinue={(email) => updateSettings({ ...settings, email, onboarded: true })} />
      )}
    </AppContext.Provider>
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
  fullLoader: {
    flex: 1,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
    backgroundColor: colors.background,
  },
  headerTop: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.sm,
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
  login: {
    flex: 1,
    justifyContent: "center",
    gap: spacing.md,
    padding: spacing.lg,
  },
  loginTitle: {
    color: colors.ink,
    fontSize: 34,
    fontWeight: "800",
    letterSpacing: 0,
  },
  languageRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.xs,
  },
  languageLabel: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
    marginRight: spacing.xs,
  },
  languageButton: {
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  languageButtonActive: {
    backgroundColor: colors.graphite,
    borderColor: colors.graphite,
  },
  languageText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800",
  },
  languageTextActive: {
    color: colors.lime,
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
    flex: 1,
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
