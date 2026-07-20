import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";

type AppStatus = "starting" | "starting_api" | "healthy" | "error";

interface HealthResponse {
  status: string;
  version: string;
}

function App() {
  const [status, setStatus] = useState<AppStatus>("starting");
  const [apiPort, setApiPort] = useState(8000);
  const [errorMessage, setErrorMessage] = useState("");
  const [appVersion, setAppVersion] = useState("");

  const checkHealth = useCallback(async () => {
    try {
      const healthy = await invoke<boolean>("check_api_health");
      if (healthy) {
        const health = await invoke<HealthResponse>("get_api_health");
        setAppVersion(health.version);
        setStatus("healthy");
        return true;
      }
    } catch {
      // API not ready yet
    }
    return false;
  }, []);

  useEffect(() => {
    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout>;

    async function bootstrap() {
      setStatus("starting_api");

      // Poll for API health every 1.5s for up to 30s
      let attempts = 0;
      const maxAttempts = 20;

      const poll = async () => {
        if (cancelled) return;
        attempts++;

        const ok = await checkHealth();
        if (ok) {
          setStatus("healthy");
          return;
        }

        if (attempts >= maxAttempts) {
          if (!cancelled) {
            setStatus("error");
            setErrorMessage(
              "API did not start within the expected time. " +
                "Ensure the AstroOS API is accessible at localhost:8000.",
            );
          }
          return;
        }

        pollTimer = setTimeout(poll, 1500);
      };

      // Start polling after a brief initial delay
      pollTimer = setTimeout(poll, 1000);

      // Get the configured API port
      try {
        const port = await invoke<number>("get_api_port");
        setApiPort(port);
      } catch {
        // Use default
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
      clearTimeout(pollTimer);
    };
  }, [checkHealth]);

  const handleRetry = () => {
    setStatus("starting_api");
    setErrorMessage("");
    setTimeout(() => checkHealth(), 1000);
  };

  // ── Loading screen while API starts ──────────────────────────────────
  if (status !== "healthy") {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          color: "#e2e8f0",
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          gap: "24px",
        }}
      >
        <div
          style={{
            fontSize: "48px",
            fontWeight: 700,
            background: "linear-gradient(135deg, #f59e0b, #d97706)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.02em",
          }}
        >
          AstroOS
        </div>

        {status === "starting_api" && (
          <>
            <div style={{ fontSize: "14px", color: "#94a3b8" }}>
              Starting API on port {apiPort}...
            </div>
            <div
              style={{
                width: "32px",
                height: "32px",
                border: "3px solid #334155",
                borderTopColor: "#f59e0b",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </>
        )}

        {status === "error" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "12px",
              maxWidth: "480px",
              textAlign: "center",
            }}
          >
            <div style={{ color: "#ef4444", fontSize: "14px" }}>
              {errorMessage}
            </div>
            <button
              onClick={handleRetry}
              style={{
                padding: "8px 24px",
                borderRadius: "6px",
                border: "1px solid #f59e0b",
                background: "transparent",
                color: "#f59e0b",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              Retry
            </button>
          </div>
        )}
      </div>
    );
  }

  // ── Main app: embed the Next.js frontend ────────────────────────────
  const iframeSrc =
    import.meta.env.DEV
      ? "http://localhost:3000"
      : `http://localhost:${apiPort}/api/desktop-index.html`;

  return (
    <div style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Title bar area — could be extended with custom decorations */}
      <div
        style={{
          display: "none",
          height: "0px",
          background: "#0f172a",
          borderBottom: "1px solid #1e293b",
        }}
        data-tauri-drag-region
      />
      {/* Main content iframe */}
      <iframe
        src={iframeSrc}
        style={{
          flex: 1,
          width: "100%",
          border: "none",
          background: "#0f172a",
        }}
        title="AstroOS"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
}

export default App;
