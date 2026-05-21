import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { apiPost } from "../lib/api";
import { trackEvent } from "../lib/analytics";
import { requestNotificationPermission, scheduleNotification } from "../lib/notifications";

type PublicAiAction = {
  label: string;
  path: string;
  description: string;
};

type PublicAiChatResponse = {
  reply: string;
  suggested_actions: PublicAiAction[];
  intent?: string | null;
  slots?: Record<string, string>;
  missing_fields?: string[];
  next_question?: string | null;
  execution_ready?: boolean;
  execution_type?: string | null;
  execution_label?: string | null;
  confirmation_prompt?: string | null;
  execution_path?: string | null;
  execution_payload?: Record<string, string>;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  created_at: string;
  intent?: string | null;
  slots?: Record<string, string>;
  missing_fields?: string[];
  next_question?: string | null;
  execution_ready?: boolean;
  execution_type?: string | null;
  execution_label?: string | null;
  confirmation_prompt?: string | null;
  execution_path?: string | null;
  execution_payload?: Record<string, string>;
};

type ChatThread = {
  id: string;
  title: string;
  pinned: boolean;
  messages: ChatMessage[];
  updated_at: string;
  summary?: string;
};

type WorkflowPreset = {
  id: string;
  title: string;
  description: string;
  prompt: string;
  path: string;
};

type IntentSnapshot = {
  intent: string | null;
  slots: Record<string, string>;
  missingFields: string[];
  nextQuestion: string | null;
  executionReady: boolean;
  executionType: string | null;
  executionLabel: string | null;
  confirmationPrompt: string | null;
  executionPath: string | null;
  executionPayload: Record<string, string>;
};

type SlotReplySuggestion = {
  label: string;
  text: string;
};

type AiChatPreferences = {
  defaultRecipientAlias: string;
  defaultTransferAmount: string;
  defaultReminderMinutes: number;
};

function formatMoneyLike(value: number): string {
  if (!Number.isFinite(value)) return "0";
  const rounded = Math.round(value * 100) / 100;
  if (Math.abs(rounded - Math.round(rounded)) < 0.000001) return `${Math.round(rounded)}`;
  return `${rounded}`;
}

function titleCaseWords(raw: string): string {
  const text = raw.trim();
  if (!text) return text;
  return text
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function shortValue(value: string, max = 18): string {
  const clean = value.trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max - 1)}…`;
}

function buildRecipientChangeOptions(currentRecipient: string): SlotReplySuggestion[] {
  const clean = currentRecipient.trim();
  if (!clean) return [];
  const isAddress = /^0x[a-fA-F0-9]{40}$/.test(clean);
  const currentLabel = shortValue(clean, 16);

  if (isAddress) {
    return [
      { label: `Change ${currentLabel} -> Alex`, text: "Change recipient to Alex" },
      { label: `Change ${currentLabel} -> 0xABCD...`, text: "Change recipient to 0xabcd1234abcd1234abcd1234abcd1234abcd1234" },
    ];
  }
  return [
    { label: `Change ${currentLabel} -> Jordan`, text: "Change recipient to Jordan" },
    { label: `Change ${currentLabel} -> 0xABCD...`, text: "Change recipient to 0xabcd1234abcd1234abcd1234abcd1234abcd1234" },
  ];
}

function buildRenameOptions(currentTitle: string): SlotReplySuggestion[] {
  const base = currentTitle.trim();
  if (!base) return [];
  const titleVariantA = `Updated ${base}`;
  const titleVariantB = `${base} Review`;
  return [
    { label: `Rename -> ${shortValue(titleVariantA, 20)}`, text: `Rename event to "${titleVariantA}"` },
    { label: `Rename -> ${shortValue(titleVariantB, 20)}`, text: `Rename event to "${titleVariantB}"` },
  ];
}

const AI_CHAT_THREADS_KEY = "victory_ai_chat_threads";
const AI_CHAT_ACTIVE_THREAD_KEY = "victory_ai_chat_active_thread";
const AI_CHAT_PREFERENCES_KEY = "victory_ai_chat_preferences";
const CALENDAR_EVENTS_KEY = "victory_calendar_events";
const HISTORY_RECENT_WINDOW = 12;
const HISTORY_SUMMARY_TRIGGER = 16;

const WORKFLOWS: WorkflowPreset[] = [
  {
    id: "send-vusd",
    title: "Send vUSD Workflow",
    description: "Get exact steps to transfer vUSD and verify confirmation.",
    prompt: "Walk me through sending vUSD to a friend and verifying the transfer.",
    path: "/wallet/send",
  },
  {
    id: "news-briefing",
    title: "News Briefing",
    description: "Summarize the latest launch and impact updates.",
    prompt: "Give me a short briefing from our latest news and impact updates.",
    path: "/news",
  },
  {
    id: "launch-calendar",
    title: "Launch Planner",
    description: "Create a schedule plan for launch tasks and reminders.",
    prompt: "Help me build a launch schedule with milestones and reminder timing.",
    path: "/calendar",
  },
  {
    id: "social-game",
    title: "Community + Gaming Plan",
    description: "Plan social sessions and game events for engagement.",
    prompt: "Create a community plan using social rooms and gaming sessions this week.",
    path: "/social",
  },
];

function newThread(seedTitle = "New Thread"): ChatThread {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    title: seedTitle,
    pinned: false,
    updated_at: new Date().toISOString(),
    messages: [
      {
        role: "assistant",
        content: "Victory AI is online. Ask about vUSD, social, gaming, news, calendar, or donations.",
        created_at: new Date().toISOString(),
      },
    ],
    summary: "",
  };
}

function loadThreads(): ChatThread[] {
  if (typeof window === "undefined") return [newThread("Primary Thread")];
  try {
    const raw = window.localStorage.getItem(AI_CHAT_THREADS_KEY);
    if (!raw) return [newThread("Primary Thread")];
    const parsed = JSON.parse(raw) as ChatThread[];
    if (!Array.isArray(parsed) || !parsed.length) return [newThread("Primary Thread")];
    return parsed;
  } catch {
    return [newThread("Primary Thread")];
  }
}

function saveThreads(threads: ChatThread[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AI_CHAT_THREADS_KEY, JSON.stringify(threads.slice(0, 40)));
}

function loadActiveThreadId(threads: ChatThread[]): string {
  if (typeof window === "undefined") return threads[0].id;
  const stored = window.localStorage.getItem(AI_CHAT_ACTIVE_THREAD_KEY);
  const exists = threads.some((thread) => thread.id === stored);
  return exists && stored ? stored : threads[0].id;
}

function saveActiveThreadId(id: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AI_CHAT_ACTIVE_THREAD_KEY, id);
}

function loadPreferences(): AiChatPreferences {
  const defaults: AiChatPreferences = {
    defaultRecipientAlias: "Alex",
    defaultTransferAmount: "25",
    defaultReminderMinutes: 15,
  };
  if (typeof window === "undefined") return defaults;
  try {
    const raw = window.localStorage.getItem(AI_CHAT_PREFERENCES_KEY);
    if (!raw) return defaults;
    const parsed = JSON.parse(raw) as Partial<AiChatPreferences>;
    return {
      defaultRecipientAlias: (parsed.defaultRecipientAlias ?? defaults.defaultRecipientAlias).toString().trim() || defaults.defaultRecipientAlias,
      defaultTransferAmount: (parsed.defaultTransferAmount ?? defaults.defaultTransferAmount).toString().trim() || defaults.defaultTransferAmount,
      defaultReminderMinutes: Number.isFinite(Number(parsed.defaultReminderMinutes))
        ? Number(parsed.defaultReminderMinutes)
        : defaults.defaultReminderMinutes,
    };
  } catch {
    return defaults;
  }
}

function savePreferences(preferences: AiChatPreferences): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AI_CHAT_PREFERENCES_KEY, JSON.stringify(preferences));
}

function summarizeHistorySlice(messages: ChatMessage[]): string {
  const compact = messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .slice(-16)
    .map((message) => `${message.role}: ${message.content.replace(/\s+/g, " ").trim().slice(0, 120)}`);
  return compact.join(" | ").slice(0, 1000);
}

function updateThreadSummary(thread: ChatThread): ChatThread {
  if (!thread.messages.length || thread.messages.length <= HISTORY_SUMMARY_TRIGGER) {
    return thread.summary ? { ...thread, summary: "" } : thread;
  }
  const older = thread.messages.slice(0, Math.max(0, thread.messages.length - HISTORY_RECENT_WINDOW));
  const olderSummary = summarizeHistorySlice(older);
  const merged = [thread.summary?.trim(), olderSummary].filter(Boolean).join(" || ").slice(-1400);
  return { ...thread, summary: merged };
}

function buildHistoryForApi(thread: ChatThread): string[] {
  const recent = thread.messages.slice(-HISTORY_RECENT_WINDOW).map((message) => `${message.role}: ${message.content}`);
  if (thread.summary?.trim()) {
    return [`system: conversation_summary ${thread.summary.trim()}`, ...recent];
  }
  return recent;
}

function formatDateTimeLocal(value: Date): string {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  const hour = `${value.getHours()}`.padStart(2, "0");
  const minute = `${value.getMinutes()}`.padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function normalizeCalendarDateDraft(raw: string): string {
  const value = raw.trim();
  if (!value) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return `${value}T09:00`;
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) return value.slice(0, 16);
  const lowered = value.toLowerCase();
  const now = new Date();
  const base = new Date(now.getTime());
  base.setSeconds(0, 0);
  if (lowered === "today") return formatDateTimeLocal(base);
  if (lowered === "tomorrow") {
    base.setDate(base.getDate() + 1);
    return formatDateTimeLocal(base);
  }
  if (lowered === "next week") {
    base.setDate(base.getDate() + 7);
    return formatDateTimeLocal(base);
  }
  if (lowered === "next month") {
    base.setMonth(base.getMonth() + 1);
    return formatDateTimeLocal(base);
  }
  return "";
}

const CHAT_BOOTSTRAP = (() => {
  const seeded = loadThreads();
  return {
    threads: seeded,
    activeThreadId: loadActiveThreadId(seeded),
  };
})();

function buildIntentDraftPath(snapshot: IntentSnapshot | null): string | null {
  if (!snapshot?.intent) return null;
  const params = new URLSearchParams();

  if (snapshot.intent === "send_vusd") {
    const recipient = snapshot.slots.recipient?.trim();
    const amount = snapshot.slots.amount?.trim();
    const currency = snapshot.slots.currency?.trim();
    if (recipient) params.set("recipient", recipient);
    if (amount) params.set("amount", amount);
    if (currency) params.set("currency", currency);
    const query = params.toString();
    return query ? `/wallet/send?${query}` : "/wallet/send";
  }

  if (snapshot.intent === "create_calendar_event") {
    const title = snapshot.slots.title?.trim();
    const date = snapshot.slots.date?.trim();
    if (title) params.set("title", title);
    if (date) params.set("date", date);
    const query = params.toString();
    return query ? `/calendar?${query}` : "/calendar";
  }

  return null;
}

function buildSlotReplySuggestions(snapshot: IntentSnapshot | null, preferences: AiChatPreferences): SlotReplySuggestion[] {
  if (!snapshot?.intent) return [];
  const missing = new Set(snapshot.missingFields);

  if (snapshot.intent === "send_vusd") {
    const amountValue = Number(snapshot.slots.amount ?? "");
    const hasAmount = Number.isFinite(amountValue) && amountValue > 0;
    const recipient = snapshot.slots.recipient?.trim();

    if (missing.has("recipient") && missing.has("amount")) {
      const alias = preferences.defaultRecipientAlias || "Alex";
      const amount = preferences.defaultTransferAmount || "25";
      return [
        { label: `${amount} to ${alias}`, text: `Send ${amount} vUSD to ${alias}` },
        { label: "100 to 0x...", text: "Send 100 vUSD to 0x1234567890abcdef1234567890abcdef12345678" },
      ];
    }
    if (missing.has("recipient")) {
      const alias = preferences.defaultRecipientAlias || "Alex";
      return [
        { label: `Recipient ${alias}`, text: `Recipient is ${alias}` },
        { label: "Recipient 0x...", text: "Send to 0x1234567890abcdef1234567890abcdef12345678" },
      ];
    }
    if (missing.has("amount")) {
      const amount = preferences.defaultTransferAmount || "25";
      return [
        { label: `Amount ${amount}`, text: `Amount is ${amount} vUSD` },
        { label: "Amount 100", text: "Amount is 100 vUSD" },
      ];
    }

    if (recipient && hasAmount) {
      const bump = Math.max(1, amountValue * 0.25);
      const lowerTo = Math.max(1, amountValue * 0.5);
      const raiseTo = amountValue + bump;
      const raiseLabel = formatMoneyLike(raiseTo);
      const lowerLabel = formatMoneyLike(lowerTo);
      const currentLabel = formatMoneyLike(amountValue);
      const currency = snapshot.slots.currency?.trim().toUpperCase() || "VUSD";
      return [
        { label: `Make ${currentLabel} -> ${raiseLabel}`, text: `Make it ${raiseLabel} ${currency}` },
        { label: `Lower ${currentLabel} -> ${lowerLabel}`, text: `Lower it to ${lowerLabel} ${currency}` },
        ...buildRecipientChangeOptions(recipient),
      ];
    }
  }

  if (snapshot.intent === "create_calendar_event") {
    const title = snapshot.slots.title?.trim();
    const hasDate = !!snapshot.slots.date?.trim();
    const dateValue = snapshot.slots.date?.trim() ?? "";
    const titleLabel = title ? shortValue(titleCaseWords(title), 24) : "event";
    const dateLabel = dateValue ? shortValue(dateValue, 16) : "date";

    if (missing.has("title") && missing.has("date")) {
      return [
        { label: "Standup tomorrow", text: 'Create calendar event called "Team Standup" tomorrow' },
        { label: "Review Monday", text: 'Create calendar event called "Sprint Review" Monday' },
      ];
    }
    if (missing.has("title")) {
      return [
        { label: "Title Standup", text: 'Title is "Team Standup"' },
        { label: "Title Review", text: 'Title is "Sprint Review"' },
      ];
    }
    if (missing.has("date")) {
      const reminder = preferences.defaultReminderMinutes;
      return [
        { label: `Date tomorrow (${reminder}m reminder)`, text: "Tomorrow" },
        { label: "Date next week", text: "Next week" },
      ];
    }

    if (title && hasDate) {
      return [
        { label: `${titleLabel}: ${dateLabel} -> tomorrow`, text: "Move it to tomorrow" },
        { label: `${titleLabel}: ${dateLabel} -> next week`, text: "Move it to next week" },
        ...buildRenameOptions(title),
      ];
    }
  }

  return [];
}

export function AiChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const unreadChatFocus = searchParams.get("focus") === "unread-chat";
  const [threads, setThreads] = useState<ChatThread[]>(() => CHAT_BOOTSTRAP.threads);
  const [activeThreadId, setActiveThreadId] = useState<string>(() => CHAT_BOOTSTRAP.activeThreadId);
  const [preferences, setPreferences] = useState<AiChatPreferences>(() => loadPreferences());
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("");
  const [actions, setActions] = useState<PublicAiAction[]>([]);
  const [notificationPermission, setNotificationPermission] = useState<"granted" | "denied" | "prompt" | "unsupported">("prompt");

  const sortedThreads = useMemo(
    () =>
      [...threads].sort((a, b) => {
        if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
        return a.updated_at < b.updated_at ? 1 : -1;
      }),
    [threads]
  );

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId) ?? threads[0] ?? null,
    [activeThreadId, threads]
  );
  const activeIntentSnapshot = useMemo(() => {
    if (!activeThread) return null;
    const lastStructuredAssistant = [...activeThread.messages]
      .reverse()
      .find((message) => message.role === "assistant" && (message.intent || message.next_question || message.missing_fields?.length));
    if (!lastStructuredAssistant) return null;
    return {
      intent: lastStructuredAssistant.intent ?? null,
      slots: lastStructuredAssistant.slots ?? {},
      missingFields: lastStructuredAssistant.missing_fields ?? [],
      nextQuestion: lastStructuredAssistant.next_question ?? null,
      executionReady: !!lastStructuredAssistant.execution_ready,
      executionType: lastStructuredAssistant.execution_type ?? null,
      executionLabel: lastStructuredAssistant.execution_label ?? null,
      confirmationPrompt: lastStructuredAssistant.confirmation_prompt ?? null,
      executionPath: lastStructuredAssistant.execution_path ?? null,
      executionPayload: lastStructuredAssistant.execution_payload ?? {},
    };
  }, [activeThread]);
  const activeIntentDraftPath = useMemo(() => buildIntentDraftPath(activeIntentSnapshot), [activeIntentSnapshot]);
  const slotReplySuggestions = useMemo(
    () => buildSlotReplySuggestions(activeIntentSnapshot, preferences),
    [activeIntentSnapshot, preferences]
  );

  useEffect(() => {
    savePreferences(preferences);
  }, [preferences]);

  function commitThreads(next: ChatThread[], nextActiveId?: string) {
    setThreads(next);
    saveThreads(next);
    const activeId = nextActiveId ?? activeThreadId;
    setActiveThreadId(activeId);
    saveActiveThreadId(activeId);
  }

  function selectThread(id: string) {
    setActiveThreadId(id);
    saveActiveThreadId(id);
    setStatus("Thread selected.");
    trackEvent({
      event_name: "ai_thread_selected",
      success: true,
      metadata: { thread_id: id },
    }).catch(() => undefined);
  }

  function createThread(title?: string) {
    const thread = newThread(title ?? "New Thread");
    const next = [thread, ...threads];
    commitThreads(next, thread.id);
    setStatus("Thread created.");
    trackEvent({
      event_name: "ai_thread_created",
      success: true,
      metadata: { thread_id: thread.id, title: thread.title },
    }).catch(() => undefined);
  }

  function removeThread(id: string) {
    const next = threads.filter((thread) => thread.id !== id);
    if (!next.length) {
      const replacement = newThread("Primary Thread");
      commitThreads([replacement], replacement.id);
      setStatus("Thread removed. New primary thread created.");
      trackEvent({
        event_name: "ai_thread_deleted",
        success: true,
        metadata: { thread_id: id, created_replacement: true },
      }).catch(() => undefined);
      return;
    }
    const nextActive = id === activeThreadId ? next[0].id : activeThreadId;
    commitThreads(next, nextActive);
    setStatus("Thread removed.");
    trackEvent({
      event_name: "ai_thread_deleted",
      success: true,
      metadata: { thread_id: id, created_replacement: false },
    }).catch(() => undefined);
  }

  function togglePinned(id: string) {
    const toggledThread = threads.find((thread) => thread.id === id);
    const nextPinned = !toggledThread?.pinned;
    const next = threads.map((thread) =>
      thread.id === id ? { ...thread, pinned: nextPinned, updated_at: new Date().toISOString() } : thread
    );
    commitThreads(next);
    trackEvent({
      event_name: "ai_thread_pinned",
      success: true,
      metadata: { thread_id: id, pinned: nextPinned },
    }).catch(() => undefined);
  }

  function applyWorkflow(workflow: WorkflowPreset) {
    setInput(workflow.prompt);
    setStatus(`Workflow loaded: ${workflow.title}`);
    trackEvent({
      event_name: "ai_workflow_loaded",
      success: true,
      metadata: { workflow_id: workflow.id, path: workflow.path },
    }).catch(() => undefined);
  }

  async function enableNotifications() {
    const result = await requestNotificationPermission();
    setNotificationPermission(result);
    setStatus(result === "granted" ? "AI notifications enabled." : `Notification permission: ${result}`);
    trackEvent({
      event_name: "ai_notifications_permission",
      success: result === "granted",
      metadata: { permission: result },
    }).catch(() => undefined);
  }

  async function dispatchMessage(rawText: string, source: "input" | "slot_chip" = "input") {
    if (!activeThread) return;
    const userText = rawText.trim();
    if (!userText) return;
    const startedAt = Date.now();

    const userMessage: ChatMessage = {
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };
    const maybeTitle = activeThread.title === "New Thread" || activeThread.title === "Primary Thread"
      ? userText.slice(0, 48)
      : activeThread.title;
    const preparedThread: ChatThread = {
      ...activeThread,
      title: maybeTitle || activeThread.title,
      updated_at: new Date().toISOString(),
      messages: [...activeThread.messages, userMessage],
    };
    const summarizedPreparedThread = updateThreadSummary(preparedThread);
    const preparedThreads = threads.map((thread) => (thread.id === activeThread.id ? summarizedPreparedThread : thread));
    commitThreads(preparedThreads, preparedThread.id);
    if (source === "input") setInput("");
    setStatus("Thinking...");

    try {
      const history = buildHistoryForApi(summarizedPreparedThread);
      const payload = await apiPost<PublicAiChatResponse>("/public/ai/chat", {
        message: userText,
        history,
      });
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: payload.reply,
        created_at: new Date().toISOString(),
        intent: payload.intent ?? null,
        slots: payload.slots ?? {},
        missing_fields: payload.missing_fields ?? [],
        next_question: payload.next_question ?? null,
        execution_ready: !!payload.execution_ready,
        execution_type: payload.execution_type ?? null,
        execution_label: payload.execution_label ?? null,
        confirmation_prompt: payload.confirmation_prompt ?? null,
        execution_path: payload.execution_path ?? null,
        execution_payload: payload.execution_payload ?? {},
      };
      const nextThreads = preparedThreads.map((thread) =>
        thread.id === summarizedPreparedThread.id
          ? {
              ...thread,
              updated_at: new Date().toISOString(),
              messages: [...thread.messages, assistantMessage],
            }
          : thread
      );
      const summaryAwareThreads = nextThreads.map((thread) =>
        thread.id === summarizedPreparedThread.id ? updateThreadSummary(thread) : thread
      );
      commitThreads(summaryAwareThreads, summarizedPreparedThread.id);
      setActions(payload.suggested_actions ?? []);
      if (notificationPermission === "granted") {
        await scheduleNotification({
          title: "Victory AI Reply",
          body: payload.reply.slice(0, 160),
          source: "ai",
        });
      }
      setStatus(payload.next_question ? `Response ready. ${payload.next_question}` : "Response ready.");
      trackEvent({
        event_name: "ai_message_sent",
        success: true,
        latency_ms: Date.now() - startedAt,
        metadata: {
          thread_id: preparedThread.id,
          prompt_length: userText.length,
          suggested_actions: payload.suggested_actions?.length ?? 0,
          source,
        },
      }).catch(() => undefined);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "AI unavailable.";
      const failureMessage: ChatMessage = {
        role: "assistant",
        content: "AI service is unavailable right now. Use Apps Hub to navigate manually.",
        created_at: new Date().toISOString(),
      };
      const fallbackThreads = preparedThreads.map((thread) =>
        thread.id === preparedThread.id
          ? { ...thread, messages: [...thread.messages, failureMessage], updated_at: new Date().toISOString() }
          : thread
      );
      commitThreads(fallbackThreads, preparedThread.id);
      setStatus(detail);
      trackEvent({
        event_name: "ai_message_sent",
        success: false,
        latency_ms: Date.now() - startedAt,
        metadata: {
          thread_id: preparedThread.id,
          prompt_length: userText.length,
          reason: "ai_service_unavailable",
          source,
        },
      }).catch(() => undefined);
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await dispatchMessage(input, "input");
  }

  async function sendSlotReply(suggestion: SlotReplySuggestion) {
    const text = suggestion.text;
    await dispatchMessage(text, "slot_chip");
    trackEvent({
      event_name: "ai_slot_reply_chip_sent",
      success: true,
      metadata: {
        thread_id: activeThread?.id ?? null,
        intent: activeIntentSnapshot?.intent ?? null,
        chip_label: suggestion.label,
        text_length: text.length,
      },
    }).catch(() => undefined);
  }

  async function executeActiveIntent() {
    if (!activeIntentSnapshot || !activeIntentSnapshot.executionReady) return;
    const confirmation = activeIntentSnapshot.confirmationPrompt ?? "Execute this draft now?";
    if (!window.confirm(confirmation)) return;

    if (activeIntentSnapshot.executionType === "navigate_wallet_send") {
      const path = activeIntentSnapshot.executionPath || activeIntentDraftPath || "/wallet/send";
      navigate(path);
      setStatus("Transfer draft opened in Send vUSD.");
      trackEvent({
        event_name: "ai_execute_from_chat",
        success: true,
        metadata: { intent: activeIntentSnapshot.intent, execution_type: activeIntentSnapshot.executionType, mode: "navigate" },
      }).catch(() => undefined);
      return;
    }

    if (activeIntentSnapshot.executionType === "create_calendar_local") {
      const payload = activeIntentSnapshot.executionPayload || {};
      const title = (payload.title || activeIntentSnapshot.slots.title || "").trim();
      const rawDate = (payload.date || activeIntentSnapshot.slots.date || "").trim();
      const normalizedDate = normalizeCalendarDateDraft(rawDate) || rawDate;
      if (!title || !normalizedDate) {
        setStatus("Execution blocked: missing title or date for calendar event.");
        return;
      }
      const existingRaw = typeof window !== "undefined" ? window.localStorage.getItem(CALENDAR_EVENTS_KEY) : null;
      const existing = existingRaw ? (JSON.parse(existingRaw) as Array<Record<string, unknown>>) : [];
      const nextEvent = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        title,
        start_at: normalizedDate,
        end_at: "",
        notes: "Created from AI Chat execution",
        recurrence: "none",
        reminder_minutes: preferences.defaultReminderMinutes,
        notification_ids: [],
      };
      const updated = [...existing, nextEvent];
      if (typeof window !== "undefined") {
        window.localStorage.setItem(CALENDAR_EVENTS_KEY, JSON.stringify(updated));
      }
      setStatus(`Created calendar event '${title}' for ${normalizedDate}.`);
      trackEvent({
        event_name: "ai_execute_from_chat",
        success: true,
        metadata: { intent: activeIntentSnapshot.intent, execution_type: activeIntentSnapshot.executionType, mode: "local_create" },
      }).catch(() => undefined);
      return;
    }

    setStatus("Execution type is not supported in chat.");
  }

  return (
    <main className="container">
      <h2>AI Chat</h2>
      <p>Persistent in-house assistant with multi-thread chat and pinned workflows.</p>
      {unreadChatFocus ? (
        <section className="card" style={{ marginBottom: 12 }}>
          <strong>Unread Chat Focus</strong>
          <div>Jump into unread conversation triage now.</div>
          <Link to="/chat-room?inbox=unread">Open Unread Chat Inbox</Link>
        </section>
      ) : null}

      <section className="card" style={{ display: "grid", gap: 8 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <Link to="/">Apps Hub</Link>
          <Link to="/wallet/send">Send vUSD</Link>
          <Link to="/news">News Services</Link>
          <Link to="/calendar">Calendar</Link>
          <Link to="/social">Social</Link>
          <Link to="/gaming">Gaming</Link>
          <Link to="/notifications">Notification Center</Link>
        </div>
        <div><strong>Notification Permission:</strong> {notificationPermission}</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" onClick={enableNotifications}>Enable AI Reply Notifications</button>
          <button type="button" onClick={() => createThread()}>New Thread</button>
        </div>
      </section>

      <section className="card" style={{ marginTop: 12, display: "grid", gap: 8 }}>
        <h3 style={{ margin: 0 }}>Preferences</h3>
        <div style={{ display: "grid", gap: 8 }}>
          <input
            placeholder="Default recipient alias"
            value={preferences.defaultRecipientAlias}
            onChange={(event) =>
              setPreferences((prev) => ({
                ...prev,
                defaultRecipientAlias: event.target.value,
              }))
            }
          />
          <input
            placeholder="Default transfer amount"
            value={preferences.defaultTransferAmount}
            onChange={(event) =>
              setPreferences((prev) => ({
                ...prev,
                defaultTransferAmount: event.target.value,
              }))
            }
          />
          <input
            type="number"
            min={0}
            step={1}
            placeholder="Default reminder minutes"
            value={preferences.defaultReminderMinutes}
            onChange={(event) =>
              setPreferences((prev) => ({
                ...prev,
                defaultReminderMinutes: Number(event.target.value) || 0,
              }))
            }
          />
        </div>
      </section>

      <section className="card" style={{ marginTop: 12, display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0 }}>Pinned Workflows</h3>
        <div className="grid-4">
          {WORKFLOWS.map((workflow) => (
            <article className="card" key={workflow.id}>
              <div><strong>{workflow.title}</strong></div>
              <div>{workflow.description}</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button type="button" onClick={() => applyWorkflow(workflow)}>Use Prompt</button>
                <Link
                  to={workflow.path}
                  onClick={() =>
                    trackEvent({
                      event_name: "ai_workflow_open_service",
                      success: true,
                      metadata: { workflow_id: workflow.id, path: workflow.path },
                    }).catch(() => undefined)
                  }
                >
                  Open Service
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card" style={{ marginTop: 12, display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0 }}>Threads</h3>
        <div style={{ display: "grid", gap: 8 }}>
          {sortedThreads.map((thread) => (
            <article className="card" key={thread.id}>
              <div><strong>{thread.pinned ? "PINNED · " : ""}{thread.title}</strong></div>
              <small>{thread.messages.length} message(s) · Updated {new Date(thread.updated_at).toLocaleString()}</small>
              {thread.summary ? (
                <small>Summary memory active ({thread.summary.length} chars)</small>
              ) : null}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button type="button" onClick={() => selectThread(thread.id)}>Open</button>
                <button type="button" onClick={() => togglePinned(thread.id)}>{thread.pinned ? "Unpin" : "Pin"}</button>
                <button type="button" onClick={() => removeThread(thread.id)}>Delete</button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card" style={{ marginTop: 12, display: "grid", gap: 8 }}>
        <h3 style={{ margin: 0 }}>Conversation</h3>
        {!activeThread ? (
          <small>No active thread.</small>
        ) : (
          <>
            <div style={{ display: "grid", gap: 8 }}>
              {activeThread.messages.map((message, index) => (
                <div key={`${message.role}-${message.created_at}-${index}`} className="card">
                  <strong>{message.role === "assistant" ? "Victory AI" : "You"}</strong>
                  <div>{message.content}</div>
                  {message.role === "assistant" && message.intent ? (
                    <div style={{ marginTop: 6, fontSize: 12, opacity: 0.85 }}>
                      <div><strong>Intent:</strong> {message.intent}</div>
                      {message.slots && Object.keys(message.slots).length ? (
                        <div><strong>Slots:</strong> {Object.entries(message.slots).map(([k, v]) => `${k}=${v}`).join(", ")}</div>
                      ) : null}
                      {message.missing_fields?.length ? (
                        <div><strong>Missing:</strong> {message.missing_fields.join(", ")}</div>
                      ) : null}
                      {message.next_question ? (
                        <div><strong>Next:</strong> {message.next_question}</div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
            <form onSubmit={sendMessage} style={{ display: "grid", gap: 8 }}>
              <textarea
                rows={3}
                placeholder="Ask something..."
                value={input}
                onChange={(event) => setInput(event.target.value)}
              />
              <button type="submit">Send</button>
            </form>
            {activeIntentSnapshot ? (
              <div className="card">
                <strong>Active Workflow Context</strong>
                {activeIntentSnapshot.intent ? <div><strong>Intent:</strong> {activeIntentSnapshot.intent}</div> : null}
                {Object.keys(activeIntentSnapshot.slots).length ? (
                  <div><strong>Slots:</strong> {Object.entries(activeIntentSnapshot.slots).map(([k, v]) => `${k}=${v}`).join(", ")}</div>
                ) : (
                  <div><strong>Slots:</strong> none yet</div>
                )}
                {activeIntentSnapshot.missingFields.length ? (
                  <div><strong>Missing:</strong> {activeIntentSnapshot.missingFields.join(", ")}</div>
                ) : (
                  <div><strong>Missing:</strong> none</div>
                )}
                {activeIntentSnapshot.nextQuestion ? (
                  <div style={{ marginTop: 6 }}>
                    <strong>Prompt:</strong> {activeIntentSnapshot.nextQuestion}
                  </div>
                ) : null}
                {activeIntentDraftPath ? (
                  <div style={{ marginTop: 8 }}>
                    <Link
                      to={activeIntentDraftPath}
                      onClick={() =>
                        trackEvent({
                          event_name: "ai_intent_draft_opened",
                          success: true,
                          metadata: {
                            intent: activeIntentSnapshot.intent,
                            path: activeIntentDraftPath,
                            missing_fields: activeIntentSnapshot.missingFields.length,
                          },
                        }).catch(() => undefined)
                      }
                    >
                      Use Draft In Service
                    </Link>
                  </div>
                ) : null}
                {activeIntentSnapshot.executionReady ? (
                  <div style={{ marginTop: 8 }}>
                    <button type="button" onClick={executeActiveIntent}>
                      {activeIntentSnapshot.executionLabel || "Execute From Chat"}
                    </button>
                  </div>
                ) : null}
                {slotReplySuggestions.length ? (
                  <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {slotReplySuggestions.map((suggestion) => (
                      <button
                        key={`${suggestion.label}-${suggestion.text}`}
                        type="button"
                        onClick={() => sendSlotReply(suggestion)}
                      >
                        {suggestion.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </>
        )}
        {status ? <small>{status}</small> : null}
      </section>

      {actions.length ? (
        <section className="card" style={{ marginTop: 12, display: "grid", gap: 8 }}>
          <h3 style={{ margin: 0 }}>Suggested Actions</h3>
          <div style={{ display: "grid", gap: 8 }}>
            {actions.map((action) => (
              <article className="card" key={`${action.path}-${action.label}`}>
                <div><strong>{action.label}</strong></div>
                <div>{action.description}</div>
                <Link
                  to={action.path}
                  onClick={() =>
                    trackEvent({
                      event_name: "ai_suggested_action_opened",
                      success: true,
                      metadata: { label: action.label, path: action.path },
                    }).catch(() => undefined)
                  }
                >
                  Open
                </Link>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
