import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import pyautogui
import queue
import sys
import os
import re
import json
import platform
import ctypes

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_APP = os.path.join(PROJECT_DIR, "gui_agents", "s3", "cli_app.py")
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")
ENV_FILE = os.path.join(PROJECT_DIR, "env.txt")
HISTORY_FILE = os.path.join(PROJECT_DIR, "command_history.json")

CANDIDATE_COMMANDS = [
    "打开消息中的测试群聊，在消息发送框输入 hello，并且在聊天框点击右侧的表情图标，选择一个随机表情后发送",
    "打开云文档页面，点击新建按钮，创建空白文档",
]


def detect_platform_info() -> dict:
    """Detect platform, OS version, and architecture."""
    system = platform.system().lower()
    info = {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }
    # Friendly display name
    name_map = {"windows": "Windows", "darwin": "macOS", "linux": "Linux"}
    info["display_name"] = name_map.get(system, system.capitalize())
    return info


def detect_dpi_scale() -> float:
    """Detect OS-level DPI scaling factor (1.0 = 100%, 1.5 = 150%, etc.).

    On Windows: uses GetDpiForMonitor via shcore.dll (per-monitor aware).
    Falls back to tkinter-based detection on other platforms.
    """
    try:
        if platform.system() == "Windows":
            # Try shcore.GetDpiForMonitor (Windows 8.1+)
            shcore = ctypes.windll.shcore
            # Get primary monitor handle
            monitor = ctypes.windll.user32.MonitorFromPoint(
                ctypes.c_long(0), 1  # MONITOR_DEFAULTTOPRIMARY
            )
            dpi_x = ctypes.c_uint()
            dpi_y = ctypes.c_uint()
            result = shcore.GetDpiForMonitor(
                monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
            )
            if result == 0:  # S_OK
                # Standard DPI is 96
                return round(dpi_x.value / 96.0, 2)
    except Exception:
        pass

    # Fallback: use tkinter to measure font pixels
    try:
        root = tk.Tk()
        root.withdraw()
        # Tk default font is typically 9pt; at 96 DPI this is 12px
        # Get actual pixel height and compute DPI ratio
        font = tk.font.Font(family="TkDefaultFont")
        actual_px = font.metrics("linespace")
        dpi = root.winfo_fpixels("1i")
        root.destroy()
        return round(dpi / 96.0, 2)
    except Exception:
        return 1.0


def detect_environment() -> dict:
    """Comprehensive environment detection for first-run auto-config.

    Returns a dict with platform info, screen dimensions, DPI scaling,
    and recommended grounding resolution for each provider.
    """
    env = {}

    # Platform
    env["platform"] = detect_platform_info()

    # Screen
    sw, sh = pyautogui.size()
    env["screen_width"] = sw
    env["screen_height"] = sh

    # DPI
    env["dpi_scale"] = detect_dpi_scale()

    # Physical screen estimate
    if env["dpi_scale"] > 0:
        env["physical_width"] = int(sw * env["dpi_scale"])
        env["physical_height"] = int(sh * env["dpi_scale"])
    else:
        env["physical_width"] = sw
        env["physical_height"] = sh

    # Recommended grounding resolution per provider
    env["grounding_recommendations"] = {}
    for key, info in GROUND_PROVIDERS.items():
        image_max = info.get("image_max_dim", info.get("coord_range", 1000))
        scale = min(image_max / sw, image_max / sh, 1.0)
        env["grounding_recommendations"][key] = {
            "width": int(sw * scale),
            "height": int(sh * scale),
        }

    return env


def _parse_env_txt(path: str) -> dict:
    """Parse env.txt key: value pairs."""
    result = {}
    if not os.path.exists(path):
        return result
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
    return result

DEFAULT_CONFIG = {
    "first_run_completed": False,
    "main_provider": "volcano",
    "main_providers": {
        "volcano": {
            "model_api_key":  "",
            "model_id":       "",
            "model_url":      "https://ark.cn-beijing.volces.com/api/v3",
        },
        "openai_gpt": {
            "model_api_key":  "",
            "model_id":       "gpt-5.4",
            "model_url":      "https://right.codes/codex/v1",
        },
    },
    "ground_provider": "volcano",
    "ground_api_key": "",
    "ground_model":   "doubao-seed-1-6-vision-250815",
    "grounding_overrides": {},  # provider_key -> {width, height} manual overrides
    "detected_environment": None,  # populated on first run
}

# Main model provider routing table
MAIN_PROVIDERS = {
    "volcano": {
        "label": "火山引擎 (Doubao)",
        "provider": "openai",
        "url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "",
        "model_label": "Endpoint ID",
        "key_label": "API Key",
        "has_reasoning": False,
    },
    "openai_gpt": {
        "label": "OpenAI GPT",
        "provider": "openai",
        "url": "https://right.codes/codex/v1",
        "default_model": "gpt-5.4",
        "model_label": "模型名",
        "key_label": "API Key",
        "has_reasoning": True,
    },
}

# Grounding provider routing table — maps provider key to CLI args
GROUND_PROVIDERS = {
    "volcano": {
        "label": "火山引擎 (Doubao)",
        "provider": "openai",
        "url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-seed-1-6-vision-250815",
        "coord_range": 1000,
        "image_max_dim": 2000,
    },
    "open_router": {
        "label": "OpenRouter",
        "provider": "open_router",
        "url": "https://openrouter.ai/api/v1",
        "default_model": "bytedance/ui-tars-1.5-7b",
        "coord_range": 1920,
    },
}

def _populate_gpt_from_env(cfg: dict):
    """Pre-populate OpenAI GPT provider config from env.txt if available."""
    env = _parse_env_txt(ENV_FILE)
    gpt_cfg = cfg["main_providers"].get("openai_gpt", {})
    if env.get("oai_api") and not gpt_cfg.get("model_api_key"):
        gpt_cfg["model_api_key"] = env["oai_api"]
    if env.get("oai_base_url") and gpt_cfg.get("model_url") == "https://right.codes/codex/v1":
        gpt_cfg["model_url"] = env["oai_base_url"]
    if env.get("model") and gpt_cfg.get("model_id") == "gpt-5.4":
        gpt_cfg["model_id"] = env["model"]


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Migrate old flat config to new per-provider structure
            if "main_providers" not in saved:
                old_key = saved.pop("model_api_key", "")
                old_id = saved.pop("model_id", "")
                old_url = saved.pop("model_url", DEFAULT_CONFIG["main_providers"]["volcano"]["model_url"])
                saved["main_providers"] = {
                    "volcano": {
                        "model_api_key": old_key,
                        "model_id": old_id,
                        "model_url": old_url,
                    },
                    "openai_gpt": {
                        "model_api_key": "",
                        "model_id": "gpt-5.4",
                        "model_url": "https://right.codes/codex/v1",
                    },
                }
            # Ensure all known providers exist
            for pk, defaults in DEFAULT_CONFIG["main_providers"].items():
                if pk not in saved["main_providers"]:
                    saved["main_providers"][pk] = defaults.copy()
            # Ensure new top-level keys exist
            for key in ("first_run_completed", "grounding_overrides", "detected_environment"):
                if key not in saved:
                    saved[key] = DEFAULT_CONFIG[key]
            cfg = {**DEFAULT_CONFIG, **saved}
            _populate_gpt_from_env(cfg)
            return cfg
        except Exception:
            pass
    cfg = DEFAULT_CONFIG.copy()
    _populate_gpt_from_env(cfg)
    return cfg


def run_first_run_setup(cfg: dict):
    """Run environment detection on first launch and persist results."""
    try:
        env = detect_environment()
        cfg["detected_environment"] = env
        cfg["first_run_completed"] = True
        # Auto-set grounding resolution from recommendations
        provider = cfg.get("ground_provider", "volcano")
        recs = env.get("grounding_recommendations", {})
        if provider in recs:
            cfg.setdefault("grounding_overrides", {})
            # Only auto-set if user hasn't manually overridden
            if provider not in cfg["grounding_overrides"]:
                cfg["grounding_overrides"][provider] = recs[provider]
        save_config(cfg)
        return env
    except Exception:
        cfg["first_run_completed"] = True
        cfg["detected_environment"] = {}
        save_config(cfg)
        return {}

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent S 启动器")
        self.root.resizable(True, True)
        self.process = None
        self.output_queue = queue.Queue()
        self.agent_ready = False
        self.cfg = load_config()
        self.command_history = self._load_command_history()

        # First-run: auto-detect environment and save config
        if not self.cfg.get("first_run_completed"):
            self._run_first_run_setup()

        self._build_ui()
        self._load_resolution_from_config()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        # Tab 1: Agent
        agent_tab = ttk.Frame(notebook)
        notebook.add(agent_tab, text="  Agent  ")
        self._build_agent_tab(agent_tab)

        # Tab 2: SOP quick-actions
        sop_tab = ttk.Frame(notebook)
        notebook.add(sop_tab, text="  快捷操作  ")
        self._build_sop_tab(sop_tab)

        self.root.update_idletasks()
        self.root.minsize(660, 600)

    # ── Agent tab ────────────────────────────────────────────────────────────

    def _build_agent_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # ── 顶部：配置区 ──
        cfg = ttk.LabelFrame(parent, text="配置", padding=8)
        cfg.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))
        cfg.columnconfigure(1, weight=1)

        # ── Main model provider selector ──
        row = 0
        ttk.Label(cfg, text="主模型").grid(row=row, column=0, sticky="w", pady=2)
        main_frame = ttk.Frame(cfg)
        main_frame.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        saved_main_key = self.cfg.get("main_provider", "volcano")
        saved_main_label = MAIN_PROVIDERS.get(saved_main_key, MAIN_PROVIDERS["volcano"])["label"]
        self.v_main_provider = tk.StringVar(value=saved_main_label)
        main_names = [p["label"] for p in MAIN_PROVIDERS.values()]
        self._main_provider_keys = list(MAIN_PROVIDERS.keys())
        self.cb_main_provider = ttk.Combobox(
            main_frame, textvariable=self.v_main_provider,
            values=main_names, state="readonly", width=22
        )
        self.cb_main_provider.pack(side="left")
        self.cb_main_provider.bind("<<ComboboxSelected>>", self._on_main_provider_changed)

        # ── Main model key (label dynamic) ──
        row += 1
        self.v_main_key_label = tk.StringVar(value=self._current_main_provider()["key_label"])
        ttk.Label(cfg, textvariable=self.v_main_key_label).grid(row=row, column=0, sticky="w", pady=2)
        self.v_model_key = tk.StringVar(value=self._current_main_config()["model_api_key"])
        ttk.Entry(cfg, textvariable=self.v_model_key, show="*", width=50).grid(row=row, column=1, sticky="ew", padx=(8, 0))

        # ── Main model name/ID (label dynamic) ──
        row += 1
        self.v_main_model_label = tk.StringVar(value=self._current_main_provider()["model_label"])
        ttk.Label(cfg, textvariable=self.v_main_model_label).grid(row=row, column=0, sticky="w", pady=2)
        model_main_frame = ttk.Frame(cfg)
        model_main_frame.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self.v_model_id = tk.StringVar(value=self._current_main_config()["model_id"])
        ttk.Entry(model_main_frame, textvariable=self.v_model_id, width=40).pack(side="left")
        self.btn_reset_main_model = ttk.Button(
            model_main_frame, text="重置为默认",
            command=self._reset_main_model, width=10
        )
        self.btn_reset_main_model.pack(side="left", padx=(4, 0))

        # ── Grounding provider separator ──
        row += 1
        ttk.Separator(cfg, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        # ── Grounding provider selector ──
        row += 1
        ttk.Label(cfg, text="定位服务").grid(row=row, column=0, sticky="w", pady=2)
        prov_frame = ttk.Frame(cfg)
        prov_frame.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        saved_provider_key = self.cfg.get("ground_provider", "volcano")
        saved_provider_label = GROUND_PROVIDERS.get(
            saved_provider_key, GROUND_PROVIDERS["volcano"]
        )["label"]
        self.v_ground_provider = tk.StringVar(value=saved_provider_label)
        provider_names = [p["label"] for p in GROUND_PROVIDERS.values()]
        self._provider_keys = list(GROUND_PROVIDERS.keys())
        self.cb_provider = ttk.Combobox(
            prov_frame, textvariable=self.v_ground_provider,
            values=provider_names, state="readonly", width=22
        )
        self.cb_provider.pack(side="left")
        self.cb_provider.bind("<<ComboboxSelected>>", self._on_provider_changed)

        row += 1
        self.v_ground_label = tk.StringVar(
            value=self._current_provider()["label"] + " API Key"
        )
        ttk.Label(cfg, textvariable=self.v_ground_label).grid(row=row, column=0, sticky="w", pady=2)
        self.v_ground_key = tk.StringVar(value=self.cfg["ground_api_key"])
        ttk.Entry(cfg, textvariable=self.v_ground_key, show="*", width=50).grid(row=row, column=1, sticky="ew", padx=(8, 0))

        row += 1
        ttk.Label(cfg, text="定位模型名").grid(row=row, column=0, sticky="w", pady=2)
        model_frame = ttk.Frame(cfg)
        model_frame.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        self.v_ground_model = tk.StringVar(value=self.cfg["ground_model"])
        ttk.Entry(model_frame, textvariable=self.v_ground_model, width=40).pack(side="left")
        ttk.Button(model_frame, text="重置为默认",
                   command=self._reset_ground_model, width=10).pack(side="left", padx=(4, 0))

        row += 1
        ttk.Label(cfg, text="定位分辨率").grid(row=row, column=0, sticky="w", pady=2)
        res_frame = ttk.Frame(cfg)
        res_frame.grid(row=row, column=1, sticky="w", padx=(8, 0))
        self.v_gw = tk.StringVar()
        self.v_gh = tk.StringVar()
        ttk.Entry(res_frame, textvariable=self.v_gw, width=6).pack(side="left")
        ttk.Label(res_frame, text=" x ").pack(side="left")
        ttk.Entry(res_frame, textvariable=self.v_gh, width=6).pack(side="left")
        self.v_screen_info = tk.StringVar()
        ttk.Label(res_frame, textvariable=self.v_screen_info, foreground="gray").pack(side="left", padx=(10, 0))

        row += 1
        ttk.Label(cfg, text="系统环境").grid(row=row, column=0, sticky="w", pady=2)
        env_frame = ttk.Frame(cfg)
        env_frame.grid(row=row, column=1, sticky="w", padx=(8, 0))
        self.v_env_info = tk.StringVar()
        ttk.Label(env_frame, textvariable=self.v_env_info, foreground="gray").pack(side="left")
        self.btn_redetect = ttk.Button(
            env_frame, text="重新检测环境", command=self._redetect_environment, width=14
        )
        self.btn_redetect.pack(side="left", padx=(12, 0))

        row += 1
        btn_frame = ttk.Frame(cfg)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(8, 0))
        self.btn_start = ttk.Button(btn_frame, text="▶  启动 Agent", command=self._start_agent, width=20)
        self.btn_start.pack(side="left", padx=4)
        self.btn_stop = ttk.Button(btn_frame, text="■  停止", command=self._stop_agent, width=10, state="disabled")
        self.btn_stop.pack(side="left", padx=4)
        ttk.Button(btn_frame, text="💾 保存配置", command=self._save_config, width=12).pack(side="left", padx=4)
        self.v_status = tk.StringVar(value="未启动")
        ttk.Label(btn_frame, textvariable=self.v_status, foreground="gray").pack(side="left", padx=12)

        # ── 中部：日志区 ──
        log_frame = ttk.LabelFrame(parent, text="运行日志", padding=4)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = scrolledtext.ScrolledText(log_frame, wrap="word", height=18,
                                             font=("Consolas", 9), state="disabled",
                                             bg="#1e1e1e", fg="#d4d4d4",
                                             insertbackground="white")
        self.log.grid(row=0, column=0, sticky="nsew")

        self.log.tag_config("info",    foreground="#9cdcfe")
        self.log.tag_config("action",  foreground="#4ec9b0")
        self.log.tag_config("warn",    foreground="#ce9178")
        self.log.tag_config("query",   foreground="#dcdcaa")
        self.log.tag_config("success", foreground="#6a9955")
        self.log.tag_config("normal",  foreground="#d4d4d4")

        # ── 底部：指令输入区 ──
        input_frame = ttk.LabelFrame(parent, text="任务指令", padding=6)
        input_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 4))
        input_frame.columnconfigure(0, weight=1)

        self.v_query = tk.StringVar()
        self.cb_query = ttk.Combobox(input_frame, textvariable=self.v_query, font=("Microsoft YaHei", 11))
        self.cb_query.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.cb_query.bind("<Return>", lambda e: self._send_query())
        self.cb_query["values"] = self.command_history
        self.cb_query.configure(state="disabled")

        self.btn_send = ttk.Button(input_frame, text="发送", command=self._send_query, width=10, state="disabled")
        self.btn_send.grid(row=0, column=1)

    # ── SOP tab ───────────────────────────────────────────────────────────────

    def _build_sop_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # toolbar
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        ttk.Button(toolbar, text="🔄 刷新列表", command=self._reload_sops).pack(side="left")
        ttk.Label(toolbar, text="  点击卡片填写参数并执行", foreground="gray").pack(side="left")

        # scrollable card area
        canvas = tk.Canvas(parent, highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        vsb.grid(row=1, column=1, sticky="ns", pady=4)
        canvas.configure(yscrollcommand=vsb.set)

        self._sop_frame = ttk.Frame(canvas)
        self._sop_frame_id = canvas.create_window((0, 0), window=self._sop_frame, anchor="nw")
        self._sop_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._sop_frame_id, width=e.width))
        # mouse wheel
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # SOP execution log
        log_frame = ttk.LabelFrame(parent, text="执行日志", padding=4)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))
        log_frame.columnconfigure(0, weight=1)

        self.sop_log = scrolledtext.ScrolledText(log_frame, wrap="word", height=8,
                                                 font=("Consolas", 9), state="disabled",
                                                 bg="#1e1e1e", fg="#d4d4d4")
        self.sop_log.grid(row=0, column=0, sticky="ew")
        self.sop_log.tag_config("ok",   foreground="#6a9955")
        self.sop_log.tag_config("err",  foreground="#ce9178")
        self.sop_log.tag_config("info", foreground="#9cdcfe")

        self._reload_sops()

    def _reload_sops(self):
        from sop_executor import list_sops
        for w in self._sop_frame.winfo_children():
            w.destroy()
        sops = list_sops()
        if not sops:
            ttk.Label(self._sop_frame,
                      text="sops/ 目录为空，请在其中添加 JSON 文件",
                      foreground="gray").pack(padx=12, pady=20)
            return
        for sop in sops:
            self._make_sop_card(sop)

    def _make_sop_card(self, sop: dict):
        card = ttk.LabelFrame(self._sop_frame,
                              text=sop.get("name", "未命名"),
                              padding=8)
        card.pack(fill="x", padx=6, pady=4)
        card.columnconfigure(1, weight=1)

        desc = sop.get("description", "")
        if desc:
            ttk.Label(card, text=desc, foreground="gray",
                      wraplength=500, justify="left").grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        param_vars = {}
        for i, p in enumerate(sop.get("params", []), start=1):
            ttk.Label(card, text=p["label"]).grid(row=i, column=0, sticky="w", padx=(0, 8))
            var = tk.StringVar()
            entry = ttk.Entry(card, textvariable=var, width=40)
            entry.grid(row=i, column=1, sticky="ew")
            if p.get("placeholder"):
                entry.insert(0, p["placeholder"])
                entry.configure(foreground="gray")

                def _on_focus_in(e, ent=entry, ph=p["placeholder"]):
                    if ent.get() == ph:
                        ent.delete(0, "end")
                        ent.configure(foreground="")

                def _on_focus_out(e, ent=entry, v=var, ph=p["placeholder"]):
                    if not v.get():
                        ent.insert(0, ph)
                        ent.configure(foreground="gray")

                entry.bind("<FocusIn>",  _on_focus_in)
                entry.bind("<FocusOut>", _on_focus_out)

            param_vars[p["name"]] = (var, p.get("placeholder", ""))

        row_btn = max(len(sop.get("params", [])) + 1, 1)
        ttk.Button(
            card, text="▶  立即执行",
            command=lambda s=sop, pv=param_vars: self._run_sop(s, pv)
        ).grid(row=row_btn, column=0, columnspan=2, pady=(8, 0))

    def _run_sop(self, sop: dict, param_vars: dict):
        params = {}
        for name, (var, placeholder) in param_vars.items():
            val = var.get().strip()
            if val == placeholder:
                val = ""
            params[name] = val

        # check required params
        missing = [p["label"] for p in sop.get("params", [])
                   if not params.get(p["name"]) and not p.get("optional")]
        if missing:
            messagebox.showwarning("缺少参数", f"请填写：{', '.join(missing)}")
            return

        self._sop_log_write(f"\n▶ 执行：{sop.get('name')}\n", "info")

        def worker():
            from sop_executor import run_sop
            try:
                run_sop(sop, params, log_fn=lambda m: self._sop_log_write(m + "\n"))
            except Exception as e:
                self._sop_log_write(f"✗ 执行失败：{e}\n", "err")

        threading.Thread(target=worker, daemon=True).start()

    def _sop_log_write(self, text: str, tag: str = "info"):
        self.sop_log.configure(state="normal")
        if "✅" in text or "完成" in text:
            tag = "ok"
        elif "✗" in text or "错误" in text or "失败" in text:
            tag = "err"
        self.sop_log.insert("end", text, tag)
        self.sop_log.see("end")
        self.sop_log.configure(state="disabled")

    # ─── 分辨率自动检测 ───────────────────────────────────────────────────────

    # ─── main model helpers ─────────────────────────────────────────────────

    def _current_main_provider(self):
        """Return the MAIN_PROVIDERS dict for the selected main model."""
        label = self.v_main_provider.get()
        for key, info in MAIN_PROVIDERS.items():
            if info["label"] == label:
                return info
        return MAIN_PROVIDERS["volcano"]

    def _current_main_config(self):
        """Return the per-provider config dict for the selected main model."""
        key = self._main_provider_key()
        return self.cfg["main_providers"].get(key, self.cfg["main_providers"]["volcano"])

    def _main_provider_key(self):
        """Return the key (e.g. 'volcano', 'openai_gpt') for the selected main model."""
        label = self.v_main_provider.get()
        for key, info in MAIN_PROVIDERS.items():
            if info["label"] == label:
                return key
        return "volcano"

    def _on_main_provider_changed(self, event=None):
        """When main model is switched, update labels and model field."""
        info = self._current_main_provider()
        pcfg = self._current_main_config()
        self.v_main_key_label.set(info["key_label"])
        self.v_main_model_label.set(info["model_label"])
        self.v_model_key.set(pcfg["model_api_key"])
        self.v_model_id.set(pcfg["model_id"])

    def _reset_main_model(self):
        """Reset main model name to the provider default."""
        self.v_model_id.set(self._current_main_provider()["default_model"])

    # ─── grounding helpers ──────────────────────────────────────────────────

    def _current_provider(self):
        """Return the GROUND_PROVIDERS dict for the selected provider."""
        label = self.v_ground_provider.get()
        for key, info in GROUND_PROVIDERS.items():
            if info["label"] == label:
                return info
        return GROUND_PROVIDERS["volcano"]

    def _on_provider_changed(self, event=None):
        """When provider is switched, update labels, model defaults, and resolution."""
        info = self._current_provider()
        key = info["label"]
        self.v_ground_label.set(key + " API Key")
        # Reset model to provider default
        self.v_ground_model.set(info["default_model"])
        # Load saved resolution for the new provider
        self._load_resolution_from_config()

    def _reset_ground_model(self):
        """Reset grounding model name to the provider default."""
        self.v_ground_model.set(self._current_provider()["default_model"])

    def _run_first_run_setup(self):
        """Run environment detection on first launch (UI not available yet)."""
        run_first_run_setup(self.cfg)

    def _load_resolution_from_config(self):
        """Load grounding resolution: prefer saved override, then detected env, then auto-compute."""
        provider_key = self._get_ground_provider_key()
        info = self._current_provider()
        overrides = self.cfg.get("grounding_overrides", {})
        detected = self.cfg.get("detected_environment") or {}

        if provider_key in overrides:
            # User has saved override or first-run auto-set values
            ov = overrides[provider_key]
            gw, gh = ov["width"], ov["height"]
        elif detected and "grounding_recommendations" in detected:
            # Use first-run detected recommendations
            recs = detected["grounding_recommendations"]
            if provider_key in recs:
                gw, gh = recs[provider_key]["width"], recs[provider_key]["height"]
            else:
                gw, gh = self._compute_grounding_resolution(info)
        else:
            gw, gh = self._compute_grounding_resolution(info)

        self.v_gw.set(str(gw))
        self.v_gh.set(str(gh))
        self.v_screen_info.set(f"（坐标范围 0-{info['coord_range']}）")
        self._update_env_display(detected)

    def _compute_grounding_resolution(self, provider_info: dict) -> tuple:
        """Compute grounding resolution from current screen and provider limits."""
        sw, sh = pyautogui.size()
        image_max = provider_info.get("image_max_dim", provider_info.get("coord_range", 1000))
        scale = min(image_max / sw, image_max / sh, 1.0)
        return int(sw * scale), int(sh * scale)

    def _update_env_display(self, env: dict):
        """Update the environment info label."""
        if not env:
            self.v_env_info.set("")
            return
        plat = env.get("platform", {})
        os_name = plat.get("display_name", "?")
        dpi = env.get("dpi_scale", 1.0)
        sw = env.get("screen_width", 0)
        sh = env.get("screen_height", 0)
        parts = [f"{os_name}"]
        if sw and sh:
            parts.append(f"{sw}x{sh}")
        if dpi and dpi != 1.0:
            parts.append(f"缩放 {int(dpi*100)}%")
            pw = env.get("physical_width", 0)
            ph = env.get("physical_height", 0)
            if pw and ph and (pw != sw or ph != sh):
                parts.append(f"（物理 {pw}x{ph}）")
        self.v_env_info.set("  |  ".join(parts))

    def _redetect_environment(self):
        """Manual re-detect: re-scan environment and update config + UI."""
        try:
            env = detect_environment()
            self.cfg["detected_environment"] = env
            provider_key = self._get_ground_provider_key()
            recs = env.get("grounding_recommendations", {})
            if provider_key in recs:
                self.cfg.setdefault("grounding_overrides", {})
                self.cfg["grounding_overrides"][provider_key] = recs[provider_key]
                self.v_gw.set(str(recs[provider_key]["width"]))
                self.v_gh.set(str(recs[provider_key]["height"]))
            self.cfg["first_run_completed"] = True
            save_config(self.cfg)
            self._load_resolution_from_config()
            self.v_status.set("环境检测完成 ✓")
        except Exception as e:
            messagebox.showerror("检测失败", f"环境检测失败：{e}")

    def _get_ground_provider_key(self):
        """Map provider label back to key."""
        label = self.v_ground_provider.get()
        for k, v in GROUND_PROVIDERS.items():
            if v["label"] == label:
                return k
        return "volcano"

    # ─── 启动 / 停止 ──────────────────────────────────────────────────────────

    def _start_agent(self):
        if self.process and self.process.poll() is None:
            return

        self.agent_ready = False
        self._log("正在启动 Agent S...\n", "info")

        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_DIR
        env["PYTHONIOENCODING"] = "utf-8"

        main_info = self._current_main_provider()
        main_cfg = self._current_main_config()
        ground_info = self._current_provider()

        cmd = [
            sys.executable, CLI_APP,
            "--provider", main_info["provider"],
            "--model", self.v_model_id.get().strip() or main_info.get("default_model", ""),
            "--model_url", main_cfg.get("model_url", main_info["url"]),
            "--model_api_key", self.v_model_key.get().strip(),
            "--ground_provider", ground_info["provider"],
            "--ground_url", ground_info["url"],
            "--ground_api_key", self.v_ground_key.get().strip(),
            "--ground_model", self.v_ground_model.get().strip() or ground_info["default_model"],
            "--grounding_width", self.v_gw.get().strip(),
            "--grounding_height", self.v_gh.get().strip(),
        ]
        # Doubao outputs coordinates in square 0-1000 space regardless of image size.
        # Only pass coord_scale for providers that use normalized output.
        if ground_info.get("image_max_dim"):
            cmd.extend(["--ground_coord_scale", str(ground_info["coord_range"])])

        # reasoning_effort for GPT/o-series models (from env.txt, default medium)
        env_txt = _parse_env_txt(ENV_FILE)
        reasoning_effort = env_txt.get("model_reasoning_effort", "medium")
        cmd.extend(["--reasoning_effort", reasoning_effort])
        reflection_mode = env_txt.get("reflection_mode", "on_failure")
        cmd.extend(["--reflection_mode", reflection_mode])

        self.process = subprocess.Popen(
            cmd, env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            bufsize=1,
        )

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.v_status.set("运行中...")

        threading.Thread(target=self._read_output, daemon=True).start()
        self.root.after(100, self._poll_output)

    def _stop_agent(self):
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        self._set_stopped()

    def _set_stopped(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_send.configure(state="disabled")
        self.cb_query.configure(state="disabled")
        self.v_status.set("已停止")
        self._log("\n─── Agent 已停止 ───\n", "warn")

    # ─── 输出读取 ─────────────────────────────────────────────────────────────

    def _read_output(self):
        buf = ""
        while True:
            ch = self.process.stdout.read(1)
            if not ch:
                if buf:
                    self.output_queue.put(buf)
                self.output_queue.put(None)
                break
            buf += ch
            if ch == "\n" or buf.endswith("Query: ") or buf.endswith("(y/n): "):
                self.output_queue.put(buf)
                buf = ""

    def _poll_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line is None:
                    self._set_stopped()
                    return
                self._handle_line(line)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_output)

    def _handle_line(self, line: str):
        line = ANSI_ESCAPE.sub("", line)
        line_strip = line.strip()

        if line_strip.startswith("Query:"):
            if not self.agent_ready:
                self.agent_ready = True
                self._log("✅ Agent 就绪，请在下方输入任务\n", "success")
                self.btn_send.configure(state="normal")
                self.cb_query.configure(state="normal")
                self.cb_query.focus()
            return

        if "Would you like to provide another query" in line:
            self._write_stdin("y\n")
            return

        if "PLAN:" in line or "Step" in line:
            tag = "action"
        elif "ERROR" in line or "Error" in line or "Traceback" in line:
            tag = "warn"
        elif "REFLECTION" in line or "Response success" in line:
            tag = "info"
        elif "EXECUTING CODE" in line:
            tag = "query"
        else:
            tag = "normal"

        self._log(line, tag)

    # ─── 指令历史 ─────────────────────────────────────────────────────────────

    def _load_command_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        return list(CANDIDATE_COMMANDS)

    def _save_command_history(self, history: list):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_to_history(self, command: str):
        # Remove duplicates and keep most recent at top; cap at 50
        values = list(self.cb_query["values"])
        if command in values:
            values.remove(command)
        values.insert(0, command)
        if len(values) > 50:
            values = values[:50]
        self.cb_query["values"] = values
        self._save_command_history(values)

    # ─── 发送指令 ─────────────────────────────────────────────────────────────

    def _send_query(self):
        query = self.v_query.get().strip()
        if not query or not self.agent_ready:
            return
        self._log(f"\n▶ 指令：{query}\n", "query")
        self._write_stdin(query + "\n")
        self._add_to_history(query)
        self.v_query.set("")
        self.btn_send.configure(state="disabled")
        self.cb_query.configure(state="disabled")
        self.agent_ready = False

    def _write_stdin(self, text: str):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(text)
                self.process.stdin.flush()
            except Exception:
                pass

    # ─── 日志写入 ─────────────────────────────────────────────────────────────

    def _log(self, text: str, tag: str = "normal"):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    # ─── 关闭 ─────────────────────────────────────────────────────────────────

    def _save_config(self):
        # Map provider labels back to keys
        main_key = self._main_provider_key()
        provider_key = self._get_ground_provider_key()
        # Update per-provider config for current main model
        main_info = self._current_main_provider()
        self.cfg["main_providers"][main_key] = {
            "model_api_key": self.v_model_key.get().strip(),
            "model_id": self.v_model_id.get().strip(),
            "model_url": main_info["url"],
        }
        self.cfg["main_provider"] = main_key
        self.cfg["ground_provider"] = provider_key
        self.cfg["ground_api_key"] = self.v_ground_key.get().strip()
        self.cfg["ground_model"] = self.v_ground_model.get().strip()
        # Save grounding resolution override
        try:
            gw = int(self.v_gw.get().strip())
            gh = int(self.v_gh.get().strip())
            if gw > 0 and gh > 0:
                self.cfg.setdefault("grounding_overrides", {})
                self.cfg["grounding_overrides"][provider_key] = {"width": gw, "height": gh}
        except ValueError:
            pass
        save_config(self.cfg)
        self.v_status.set("配置已保存 ✓")

    def _on_close(self):
        self._stop_agent()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Launcher().run()
