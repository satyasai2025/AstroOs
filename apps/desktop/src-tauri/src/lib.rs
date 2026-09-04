use std::sync::Mutex;
use std::process::{Child, Command, Stdio};
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::time::Duration;
use tauri::{
    AppHandle, Manager, State, menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Emitter,
};

// ── Managed state ───────────────────────────────────────────────────────

struct ApiProcess {
    child: Option<Child>,
    port: u16,
}

struct AppState {
    api: Mutex<ApiProcess>,
}

// ── Configuration defaults ──────────────────────────────────────────────

const DEFAULT_API_PORT: u16 = 8000;

/// Paths to try for finding the API module, relative to the project root
/// or the bundled resource directory.
#[cfg(debug_assertions)]
const API_MODULE_PATH: &str = "apps.api.main"; // Used in dev (python -m apps.api.main)
#[cfg(debug_assertions)]
const API_WORKING_DIR: &str = "."; // Project root in dev

#[cfg(not(debug_assertions))]
const API_MODULE_PATH: &str = "api_server.app"; // Bundled resource path in release
#[cfg(not(debug_assertions))]
const API_WORKING_DIR: &str = "resources/api"; // Bundled resource dir in release

// ── Helper: check Python availability ───────────────────────────────────

/// Resolve the working directory for the bundled API process.
///
/// In dev, the API runs from the project root. In release, it runs from the
/// bundled resource directory (`resources/api` under the app's resource dir).
fn api_working_dir(resource_dir: Option<PathBuf>) -> PathBuf {
    #[cfg(debug_assertions)]
    {
        let _ = resource_dir;
        PathBuf::from(API_WORKING_DIR)
    }
    #[cfg(not(debug_assertions))]
    {
        match resource_dir {
            Some(dir) => dir.join(API_WORKING_DIR),
            None => PathBuf::from(API_WORKING_DIR),
        }
    }
}

fn find_python() -> Option<&'static str> {
    // Try python3 first, then python
    let candidates = &["python3", "python"];
    for cmd in candidates {
        if Command::new(cmd)
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .is_ok()
        {
            return Some(cmd);
        }
    }
    None
}

// ── FastAPI process management ──────────────────────────────────────────

/// Start the FastAPI server as a child process.
fn start_api(port: u16, working_dir: &PathBuf) -> Result<Child, String> {
    let python = find_python()
        .ok_or_else(|| "Python not found. Please install Python 3.11+ and ensure it is on your PATH.".to_string())?;

    let args = &[
        "-m", "uvicorn",
        API_MODULE_PATH,
        "--host", "127.0.0.1",
        "--port", &port.to_string(),
        "--log-level", "info",
    ];

    let child = Command::new(python)
        .args(args)
        .current_dir(working_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start API server: {e}"))?;

    // Spawn a background thread to capture stdout/stderr for diagnostics.
    if let Some(stdout) = child.stdout.as_ref() {
        let reader = BufReader::new(stdout.try_clone().map_err(|e| format!("Failed to clone stdout: {e}"))?);
        std::thread::spawn(move || {
            for line in reader.lines() {
                if let Ok(l) = line {
                    println!("[api:stdout] {l}");
                }
            }
        });
    }
    if let Some(stderr) = child.stderr.as_ref() {
        let reader = BufReader::new(stderr.try_clone().map_err(|e| format!("Failed to clone stderr: {e}"))?);
        std::thread::spawn(move || {
            for line in reader.lines() {
                if let Ok(l) = line {
                    eprintln!("[api:stderr] {l}");
                }
            }
        });
    }

    Ok(child)
}

/// Gracefully stop the API child process.
fn stop_api(api: &mut ApiProcess) {
    if let Some(mut child) = api.child.take() {
        // Try SIGTERM first (cross-platform: use process-kill on Windows)
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            // Send SIGTERM via kill command
            let _ = Command::new("kill")
                .arg(child.id().to_string())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();
        }
        #[cfg(windows)]
        {
            let _ = Command::new("taskkill")
                .args(["/PID", &child.id().to_string(), "/F"])
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();
        }

        // Wait for up to 5 seconds for graceful shutdown
        let _ = child.wait();
    }
}

// ── Tauri commands — exposed to the frontend ────────────────────────────

#[tauri::command]
fn start_api_server(app: tauri::AppHandle, state: State<AppState>) -> Result<String, String> {
    let mut api = state.api.lock().map_err(|e| e.to_string())?;

    if api.child.is_some() {
        return Ok("API server is already running.".to_string());
    }

    let port = api.port;
    let working_dir = api_working_dir(app.path().resource_dir().ok());
    let child = start_api(port, &working_dir)?;
    api.child = Some(child);

    Ok(format!("API server started on port {port}."))
}

#[tauri::command]
fn stop_api_server(state: State<AppState>) -> Result<String, String> {
    let mut api = state.api.lock().map_err(|e| e.to_string())?;

    if api.child.is_none() {
        return Ok("API server is not running.".to_string());
    }

    stop_api(&mut api);

    Ok("API server stopped.".to_string())
}

#[tauri::command]
fn restart_api_server(app: tauri::AppHandle, state: State<AppState>) -> Result<String, String> {
    let mut api = state.api.lock().map_err(|e| e.to_string())?;
    let port = api.port;
    let working_dir = api_working_dir(app.path().resource_dir().ok());

    stop_api(&mut api);

    let child = start_api(port, &working_dir)?;
    api.child = Some(child);

    Ok(format!("API server restarted on port {port}."))
}

#[tauri::command]
async fn check_api_health(state: State<'_, AppState>) -> Result<bool, String> {
    let port = {
        let api = state.api.lock().map_err(|e| e.to_string())?;
        api.port
    };

    let url = format!("http://127.0.0.1:{port}/api/healthz");
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .map_err(|e| format!("Failed to build HTTP client: {e}"))?;

    match client.get(&url).send().await {
        Ok(resp) => {
            Ok(resp.status().is_success())
        }
        Err(_) => Ok(false),
    }
}

#[tauri::command]
async fn get_api_health(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let port = {
        let api = state.api.lock().map_err(|e| e.to_string())?;
        api.port
    };

    let url = format!("http://127.0.0.1:{port}/api/healthz");
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .map_err(|e| format!("Failed to build HTTP client: {e}"))?;

    let resp = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Health check request failed: {e}"))?;

    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("Failed to parse health response: {e}"))?;

    Ok(body)
}

#[tauri::command]
fn get_api_port(state: State<AppState>) -> Result<u16, String> {
    let api = state.api.lock().map_err(|e| e.to_string())?;
    Ok(api.port)
}

// ── Application entry point ─────────────────────────────────────────────

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            // ── Start the API on launch ──────────────────────────────────────
            let port = DEFAULT_API_PORT;
            let handle = app.handle().clone();

            std::thread::spawn(move || {
                // Give the app window time to initialise before starting the API
                std::thread::sleep(std::time::Duration::from_secs(1));

                let working_dir = api_working_dir(handle.path().resource_dir().ok());

                // Try to start the API
                match start_api(port, &working_dir) {
                    Ok(child) => {
                        let state = handle.state::<AppState>();
                        if let Ok(mut api) = state.api.lock() {
                            api.child = Some(child);
                            let _ = handle.emit("api-status", "started");
                        } else {
                            eprintln!("[astroos-desktop] API state lock poisoned");
                        }
                    }
                    Err(e) => {
                        eprintln!("[astroos-desktop] Failed to start API: {e}");
                        let _ = handle.emit("api-error", e);
                    }
                }
            });

            // ── System tray ─────────────────────────────────────────────────
            let show_item = MenuItemBuilder::with_id("show", "Show Window")
                .build(app)?;
            let quit_item = MenuItemBuilder::with_id("quit", "Quit AstroOS")
                .build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&show_item)
                .item(&quit_item)
                .build()?;

            TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("AstroOS")
                .on_menu_event(move |app, event| {
                    match event.id().as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "quit" => {
                            // Stop the API before exiting
                            let state = app.state::<AppState>();
                            if let Ok(mut api) = state.api.lock() {
                                stop_api(&mut api);
                            }
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;

            Ok(())
        })
        .manage(AppState {
            api: Mutex::new(ApiProcess {
                child: None,
                port: DEFAULT_API_PORT,
            }),
        })
        .invoke_handler(tauri::generate_handler![
            start_api_server,
            stop_api_server,
            restart_api_server,
            check_api_health,
            get_api_health,
            get_api_port,
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                let state = app.state::<AppState>();
                if let Ok(mut api) = state.api.lock() {
                    stop_api(&mut api);
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running AstroOS desktop");
}
