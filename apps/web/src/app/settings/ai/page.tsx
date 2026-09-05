"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useAISettings, useTestAIConnection, useUpdateAISettings } from "@/lib/aiSettings";
import type { AIProvider } from "@/lib/types";
import { useEffect, useState } from "react";

const PROVIDERS: { value: AIProvider; label: string; needsApiKey: boolean }[] = [
  { value: "astroos_ai", label: "AstroOS AI", needsApiKey: false },
  { value: "gemini", label: "Google Gemini", needsApiKey: true },
  { value: "groq", label: "Groq (Ultra-Fast Llama)", needsApiKey: true },
  { value: "openai", label: "OpenAI", needsApiKey: true },
  { value: "anthropic", label: "Anthropic Claude", needsApiKey: true },
  { value: "openrouter", label: "OpenRouter", needsApiKey: true },
  { value: "ollama", label: "Ollama (Local)", needsApiKey: false },
];

const MODEL_PLACEHOLDER: Record<AIProvider, string> = {
  astroos_ai: "Server default",
  gemini: "e.g. gemini-3.6-flash",
  groq: "e.g. llama-3.3-70b-versatile",
  openai: "e.g. gpt-4o-mini",
  anthropic: "e.g. claude-sonnet-5",
  openrouter: "e.g. google/gemma-4-26b-a4b-it:free",
  ollama: "e.g. llama3.1",
};

const inputStyle = {
  backgroundColor: "var(--bg-input)",
  color: "var(--text-primary)",
  border: "1px solid var(--border-primary)",
} as const;

export default function AISettingsPage() {
  const { data: settings, isLoading } = useAISettings();
  const updateSettings = useUpdateAISettings();
  const testConnection = useTestAIConnection();

  const [provider, setProvider] = useState<AIProvider>("astroos_ai");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [temperature, setTemperature] = useState(0.3);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!settings) return;
    setProvider(settings.provider);
    setModel(settings.model ?? "");
    setBaseUrl(settings.base_url ?? "");
    setTemperature(settings.temperature);
    setMaxTokens(settings.max_tokens);
    setApiKeyInput("");
  }, [settings]);

  const providerMeta = PROVIDERS.find((p) => p.value === provider)!;

  const handleSave = () => {
    setSavedMessage(null);
    updateSettings.mutate(
      {
        provider,
        api_key: apiKeyInput || undefined,
        model: model.trim() || null,
        base_url: provider === "ollama" ? baseUrl.trim() || null : null,
        temperature,
        max_tokens: maxTokens,
      },
      {
        onSuccess: () => {
          setApiKeyInput("");
          setSavedMessage("Settings saved.");
        },
      },
    );
  };

  const handleTest = () => {
    testConnection.mutate({
      provider,
      api_key: apiKeyInput || undefined,
      model: model.trim() || null,
      base_url: provider === "ollama" ? baseUrl.trim() || null : null,
    });
  };

  if (isLoading) {
    return (
      <SettingsLayout title="AI Settings" description="Configure AI providers and model preferences">
        <div className="flex h-64 items-center justify-center" style={{ color: "var(--text-muted)" }}>
          Loading…
        </div>
      </SettingsLayout>
    );
  }

  return (
    <SettingsLayout title="AI Settings" description="Configure AI providers and model preferences">
      <div className="space-y-6">
        {/* Provider Selection */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Provider
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {PROVIDERS.map((p) => (
              <label
                key={p.value}
                className="flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-all"
                style={{
                  borderColor: provider === p.value ? "var(--accent)" : "var(--border-primary)",
                  backgroundColor: "var(--bg-input)",
                }}
              >
                <input
                  type="radio"
                  name="provider"
                  checked={provider === p.value}
                  onChange={() => setProvider(p.value)}
                  className="h-4 w-4"
                  style={{ accentColor: "var(--accent)" }}
                />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>{p.label}</span>
              </label>
            ))}
          </div>
          {provider === "astroos_ai" && (
            <p className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
              Uses AstroOS's built-in AI configuration — no API key needed.
            </p>
          )}
        </div>

        {/* API Key */}
        {providerMeta.needsApiKey && (
          <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              API Key
            </h3>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder={settings?.has_api_key ? `Stored key ending in ${settings.api_key_last4}` : "Paste your API key"}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
              autoComplete="off"
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              {settings?.has_api_key
                ? "Leave blank to keep the stored key. Type a new one to replace it."
                : "Stored encrypted. Never shown again after saving."}
            </p>
          </div>
        )}

        {/* Ollama base URL */}
        {provider === "ollama" && (
          <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              Server URL
            </h3>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:11434/v1"
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </div>
        )}

        {/* Model Settings */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Model
          </h3>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Model
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={MODEL_PLACEHOLDER[provider]}
                disabled={provider === "astroos_ai"}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none disabled:opacity-50"
                style={inputStyle}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Temperature ({temperature.toFixed(1)})
              </label>
              <input
                type="range"
                min={0}
                max={2}
                step={0.1}
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full"
                style={{ accentColor: "var(--accent)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Maximum Tokens
              </label>
              <input
                type="number"
                min={1}
                max={32000}
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </div>
          </div>
        </div>

        {testConnection.data && (
          <div
            className="rounded-lg border p-3 text-sm"
            style={{
              borderColor: testConnection.data.success ? "var(--status-success)" : "var(--status-error)",
              color: testConnection.data.success ? "var(--status-success)" : "var(--status-error)",
              backgroundColor: "var(--bg-input)",
            }}
          >
            {testConnection.data.message}
          </div>
        )}
        {updateSettings.isError && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: "var(--status-error)", color: "var(--status-error)", backgroundColor: "var(--bg-input)" }}>
            {(updateSettings.error as Error).message}
          </div>
        )}
        {savedMessage && !updateSettings.isError && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: "var(--status-success)", color: "var(--status-success)", backgroundColor: "var(--bg-input)" }}>
            {savedMessage}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={handleTest}
            disabled={testConnection.isPending}
            className="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            style={{ backgroundColor: "var(--obsidian-surface-elevated)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
          >
            {testConnection.isPending ? "Testing…" : "Test Connection"}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={updateSettings.isPending}
            className="rounded-lg px-4 py-2 text-sm font-semibold"
            style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {updateSettings.isPending ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </div>
    </SettingsLayout>
  );
}
