#!/usr/bin/env python3
"""
🐞 BugRescue Streamlit Dashboard
Premium dark-themed web UI wrapping the BugRescue V2.0 engine.
Launch: streamlit run app.py
"""
import streamlit as st
import os, sys, shutil, zipfile, io, time
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace

# --- Load .env file if present (production support) ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional — env vars can be set directly

# --- Import BugRescue engine components ---
from bug_rescue import (
    AIProvider, Executor, get_prompt, clean, generate_report,
    BACKUP_DIR, FIXED_DIR, REPORT_FILE, VERSION
)

# ============================================================
#  PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BugRescue — AI Code Surgeon",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
#  CUSTOM CSS — Glassmorphism, animations, premium design
# ============================================================
st.markdown("""
<style>
/* ---------- Google Font ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ---------- Hide default Streamlit boilerplate ---------- */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* ---------- Hero Banner ---------- */
.hero-banner {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 40%, #1a2332 70%, #0d1117 100%);
    border: 1px solid rgba(78, 201, 176, 0.15);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(78, 201, 176, 0.06) 0%, transparent 60%);
    animation: shimmer 8s ease-in-out infinite alternate;
}
@keyframes shimmer {
    0% { transform: translate(0, 0); }
    100% { transform: translate(5%, 3%); }
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4ec9b0, #6dd5c4, #3db89e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    position: relative;
    z-index: 1;
}
.hero-subtitle {
    color: #8b949e;
    font-size: 1.05rem;
    font-weight: 400;
    margin-top: 0.4rem;
    position: relative;
    z-index: 1;
}
.hero-version {
    display: inline-block;
    background: rgba(78, 201, 176, 0.12);
    color: #4ec9b0;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    border: 1px solid rgba(78, 201, 176, 0.25);
    margin-top: 0.8rem;
    position: relative;
    z-index: 1;
}

/* ---------- Glass Cards ---------- */
.glass-card {
    background: rgba(37, 37, 38, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(78, 201, 176, 0.12);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(78, 201, 176, 0.3);
    box-shadow: 0 0 20px rgba(78, 201, 176, 0.06);
}

/* ---------- Metric Cards ---------- */
.metric-card {
    background: rgba(37, 37, 38, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}
.metric-value {
    font-size: 2.8rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.metric-green .metric-value { color: #6a9955; }
.metric-red .metric-value { color: #f44747; }
.metric-amber .metric-value { color: #cca700; }
.metric-blue .metric-value { color: #569cd6; }

/* ---------- Status Badges ---------- */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-clean {
    background: rgba(106, 153, 85, 0.15);
    color: #6a9955;
    border: 1px solid rgba(106, 153, 85, 0.3);
}
.badge-fixed {
    background: rgba(78, 201, 176, 0.15);
    color: #4ec9b0;
    border: 1px solid rgba(78, 201, 176, 0.3);
}
.badge-failed {
    background: rgba(244, 71, 71, 0.15);
    color: #f44747;
    border: 1px solid rgba(244, 71, 71, 0.3);
}
.badge-skipped {
    background: rgba(204, 167, 0, 0.15);
    color: #cca700;
    border: 1px solid rgba(204, 167, 0, 0.3);
}

/* ---------- Results Table ---------- */
.results-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}
.results-table th {
    background: rgba(78, 201, 176, 0.08);
    color: #4ec9b0;
    font-weight: 600;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.9rem 1rem;
    text-align: left;
    border-bottom: 1px solid rgba(78, 201, 176, 0.15);
}
.results-table td {
    padding: 0.8rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.9rem;
    color: #d4d4d4;
}
.results-table tr:hover td {
    background: rgba(78, 201, 176, 0.03);
}
.results-table .file-name {
    font-weight: 500;
    color: #e1e4e8;
}
.results-table .error-snippet {
    color: #8b949e;
    font-size: 0.82rem;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ---------- Sidebar Enhancements ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b22 0%, #0d1117 100%) !important;
    border-right: 1px solid rgba(78, 201, 176, 0.1) !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #8b949e !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}

/* ---------- Progress Area ---------- */
.scan-status {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.8rem 1rem;
    background: rgba(37, 37, 38, 0.5);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.04);
    margin-bottom: 0.8rem;
    font-size: 0.9rem;
    color: #d4d4d4;
}
.scan-status .pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4ec9b0;
    animation: pulse-anim 1.5s ease-in-out infinite;
}
@keyframes pulse-anim {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(78,201,176,0.4); }
    50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(78,201,176,0); }
}

/* ---------- Diff View ---------- */
.diff-add { background: rgba(106, 153, 85, 0.12); color: #6a9955; }
.diff-del { background: rgba(244, 71, 71, 0.12); color: #f44747; }

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(78,201,176,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(78,201,176,0.4); }

/* ---------- Expander Styling ---------- */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  HERO BANNER
# ============================================================
def render_hero():
    st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-title">🐞 BugRescue</p>
        <p class="hero-subtitle">Autonomous AI Code Surgeon — Scan, Detect, Fix, Repeat</p>
        <span class="hero-version">{VERSION}</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
#  SIDEBAR CONFIG
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <span style="font-size: 2rem;">🐞</span>
            <p style="font-size: 1.1rem; font-weight: 700; color: #4ec9b0; margin: 0.3rem 0 0;">
                BugRescue
            </p>
            <p style="font-size: 0.72rem; color: #8b949e; margin: 0;">Configuration Panel</p>
        </div>
        <hr style="border: none; border-top: 1px solid rgba(78,201,176,0.15); margin: 0.8rem 0;">
        """, unsafe_allow_html=True)

        # Project Path
        project_path = st.text_input(
            "📁 Project Path",
            placeholder="e.g., ./my-project or D:\\Code\\app",
            help="Absolute or relative path to the project folder or single file to scan."
        )

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        # AI Provider
        provider = st.selectbox(
            "🤖 AI Provider",
            options=["ollama", "openai", "anthropic", "gemini"],
            index=0,
            help="Choose your AI backend. Ollama runs locally for full privacy."
        )

        # Conditional fields — pre-fill from environment variables
        api_key = None
        if provider != "ollama":
            env_key_name = f"{provider.upper()}_API_KEY"
            env_key_value = os.getenv(env_key_name, "")
            api_key = st.text_input(
                "🔑 API Key",
                type="password",
                value=env_key_value,
                placeholder=f"Enter your {provider.capitalize()} API key (or set {env_key_name})",
                help=f"Required for cloud providers. Auto-loaded from `{env_key_name}` env var if set."
            )

        ollama_url = None
        if provider == "ollama":
            with st.expander("⚙️ Ollama Settings", expanded=False):
                default_ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
                ollama_url = st.text_input(
                    "Server URL",
                    value=default_ollama_url,
                    help="Override if Ollama runs on a different host/port. Auto-loaded from `OLLAMA_URL` env var."
                )
                # Ollama status check
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                if st.button("🔍 Check Ollama Status", use_container_width=True):
                    try:
                        import requests
                        base_url = ollama_url.replace("/api/generate", "")
                        resp = requests.get(base_url, timeout=5)
                        if resp.status_code == 200:
                            st.success("✅ Ollama is running!")
                        else:
                            st.warning(f"⚠️ Ollama responded with status {resp.status_code}")
                    except Exception as e:
                        st.error(f"❌ Cannot reach Ollama: {e}")

        # Model override
        model_override = st.text_input(
            "🧠 Model Override",
            placeholder="Leave blank for smart default",
            help="e.g., gpt-4o, claude-3-5-sonnet, gemini-1.5-pro, qwen2.5-coder:14b"
        )

        st.markdown("<hr style='border: none; border-top: 1px solid rgba(78,201,176,0.15); margin: 1rem 0;'>", unsafe_allow_html=True)

        # Dry-run toggle
        dry_run = st.toggle("🔒 Dry-Run Mode", value=False, help="Audit only — no files will be modified.")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Start button
        start_clicked = st.button(
            "🚀 Start Rescue",
            use_container_width=True,
            type="primary"
        )

        # # Footer
        # st.markdown("""
        # <div style="position: fixed; bottom: 1rem; padding: 0.5rem; text-align: center;">
        #     <p style="font-size: 0.7rem; color: #484f58;">
        #         Safety First — Auto-backups enabled<br/>
        #         <span style="color: #4ec9b0;">BugRescue</span> © 2024
        #     </p>
        # </div>
        # """, unsafe_allow_html=True)

        return {
            "path": project_path,
            "provider": provider,
            "key": api_key or "",
            "model": model_override or None,
            "url": ollama_url,
            "dry_run": dry_run,
            "start": start_clicked,
        }


# ============================================================
#  METRICS DISPLAY
# ============================================================
def render_metrics(stats):
    total = stats['passed'] + stats['failed'] + stats['skipped']
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card metric-blue">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Scanned</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card metric-green">
            <div class="metric-value">{stats['passed']}</div>
            <div class="metric-label">Clean / Fixed</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card metric-red">
            <div class="metric-value">{stats['failed']}</div>
            <div class="metric-label">Failed</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card metric-amber">
            <div class="metric-value">{stats['skipped']}</div>
            <div class="metric-label">Skipped</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
#  RESULTS TABLE
# ============================================================
def render_results_table(logs):
    badge_map = {
        "CLEAN": "badge-clean",
        "FIXED": "badge-fixed",
        "FAILED": "badge-failed",
        "SKIPPED": "badge-skipped",
    }

    rows_html = ""
    for entry in logs:
        badge_class = badge_map.get(entry['status'], "badge-skipped")
        error_display = entry.get('error', '')[:120] or "—"
        import html
        error_display = html.escape(error_display)
        rows_html += f"""
        <tr>
            <td class="file-name">{entry['file']}</td>
            <td><span class="badge {badge_class}">{entry['status']}</span></td>
            <td class="error-snippet" title="{html.escape(entry.get('error', ''))}">{error_display}</td>
        </tr>
        """

    st.markdown(f"""
    <div class="glass-card">
        <h3 style="color: #4ec9b0; margin-top: 0; font-size: 1.1rem; font-weight: 600;">
            📋 Scan Results
        </h3>
        <table class="results-table">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Detection</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
#  FILE DETAIL EXPANDERS
# ============================================================
def render_file_details(logs, original_codes, fixed_codes):
    st.markdown("""
    <div style="margin-top: 1rem;">
        <h3 style="color: #4ec9b0; font-size: 1.1rem; font-weight: 600;">
            🔍 File Details
        </h3>
    </div>
    """, unsafe_allow_html=True)

    for entry in logs:
        fname = entry['file']
        status = entry['status']
        icon = {"CLEAN": "✅", "FIXED": "🔧", "FAILED": "❌", "SKIPPED": "⏭️"}.get(status, "📄")

        with st.expander(f"{icon} {fname} — {status}", expanded=False):
            if entry.get('error'):
                st.markdown("**Error Output:**")
                st.code(entry['error'], language="text")

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("**📄 Original Code**")
                orig = original_codes.get(fname, "")
                if orig:
                    # Detect language from extension
                    ext = Path(fname).suffix.lstrip('.')
                    lang_map = {'py': 'python', 'js': 'javascript', 'go': 'go', 'rs': 'rust',
                                'cpp': 'cpp', 'java': 'java', 'yaml': 'yaml', 'html': 'html'}
                    st.code(orig, language=lang_map.get(ext, 'text'))
                else:
                    st.caption("No source captured.")

            with col_right:
                st.markdown("**🔧 Fixed Code**")
                fixed = fixed_codes.get(fname, "")
                if fixed and status == "FIXED":
                    ext = Path(fname).suffix.lstrip('.')
                    lang_map = {'py': 'python', 'js': 'javascript', 'go': 'go', 'rs': 'rust',
                                'cpp': 'cpp', 'java': 'java', 'yaml': 'yaml', 'html': 'html'}
                    st.code(fixed, language=lang_map.get(ext, 'text'))
                elif status == "CLEAN":
                    st.success("No fix needed — code is clean!")
                elif status == "SKIPPED":
                    st.info("File was skipped (missing compiler/runtime).")
                else:
                    st.warning("AI was unable to produce a fix.")


# ============================================================
#  DOWNLOAD BUTTONS
# ============================================================
def render_downloads():
    col1, col2 = st.columns(2)

    with col1:
        # Download HTML Report
        report_path = Path(REPORT_FILE)
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            st.download_button(
                label="📊 Download HTML Report",
                data=report_content,
                file_name="bugrescue_report.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.button("📊 No Report Available", disabled=True, use_container_width=True)

    with col2:
        # Download Fixed Files as ZIP
        fixed_dir = Path(FIXED_DIR)
        if fixed_dir.exists() and any(fixed_dir.iterdir()):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fpath in fixed_dir.rglob('*'):
                    if fpath.is_file():
                        zf.write(fpath, fpath.relative_to(fixed_dir))
            zip_buffer.seek(0)
            st.download_button(
                label="📁 Download Fixed Files (ZIP)",
                data=zip_buffer,
                file_name="bugrescue_fixed_files.zip",
                mime="application/zip",
                use_container_width=True,
            )
        else:
            st.button("📁 No Fixed Files Yet", disabled=True, use_container_width=True)


# ============================================================
#  SCAN FILES (reuses bug_rescue.py logic)
# ============================================================
def scan_files(root_path):
    """Discover scannable files, same logic as bug_rescue.py main()."""
    files = []
    ignore_dirs = {BACKUP_DIR.name, FIXED_DIR.name, ".git", "__pycache__", "node_modules"}
    valid_exts = ('.py', '.js', '.go', '.rs', '.cpp', '.java', '.yaml', '.dockerfile', '.html')

    if root_path.is_file():
        if root_path.suffix.lower() in valid_exts:
            files.append(root_path)
    else:
        for r, dirs, fs in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in fs:
                if f.lower().endswith(valid_exts):
                    files.append(Path(r) / f)
    return files


# ============================================================
#  MAIN APP FLOW
# ============================================================
def main():
    render_hero()
    config = render_sidebar()

    # --- Session state defaults ---
    if 'scan_complete' not in st.session_state:
        st.session_state.scan_complete = False
    if 'stats' not in st.session_state:
        st.session_state.stats = {'passed': 0, 'failed': 0, 'skipped': 0}
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'original_codes' not in st.session_state:
        st.session_state.original_codes = {}
    if 'fixed_codes' not in st.session_state:
        st.session_state.fixed_codes = {}

    # --- Show previous results if available ---
    if st.session_state.scan_complete and not config['start']:
        render_metrics(st.session_state.stats)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        render_results_table(st.session_state.logs)
        render_file_details(st.session_state.logs, st.session_state.original_codes, st.session_state.fixed_codes)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        render_downloads()
        return

    # --- Idle state ---
    if not config['start']:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem 2rem;">
            <p style="font-size: 3rem; margin: 0;">🔬</p>
            <p style="font-size: 1.2rem; font-weight: 600; color: #e1e4e8; margin: 0.8rem 0 0.4rem;">
                Ready to Rescue
            </p>
            <p style="color: #8b949e; font-size: 0.92rem; max-width: 500px; margin: 0 auto;">
                Configure your project path and AI provider in the sidebar, then hit
                <strong style="color: #4ec9b0;">Start Rescue</strong> to begin scanning.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quick-start guide
        st.markdown("""
        <div class="glass-card" style="margin-top: 0.5rem;">
            <h3 style="color: #4ec9b0; margin-top: 0; font-size: 1rem; font-weight: 600;">
                ⚡ Quick Start
            </h3>
            <table class="results-table">
                <tr><td style="color:#569cd6; font-weight:500;">1.</td><td>Enter a project path (folder or single file)</td></tr>
                <tr><td style="color:#569cd6; font-weight:500;">2.</td><td>Pick your AI provider — <strong>Ollama</strong> for local, or a cloud API</td></tr>
                <tr><td style="color:#569cd6; font-weight:500;">3.</td><td>Click <strong style="color:#4ec9b0;">🚀 Start Rescue</strong></td></tr>
                <tr><td style="color:#569cd6; font-weight:500;">4.</td><td>Review results, download fixed files, done!</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Supported languages
        st.markdown("""
        <div class="glass-card" style="margin-top: 0.5rem;">
            <h3 style="color: #4ec9b0; margin-top: 0; font-size: 1rem; font-weight: 600;">
                🌐 Supported Languages
            </h3>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                <span class="badge badge-clean">Python</span>
                <span class="badge badge-fixed">JavaScript</span>
                <span class="badge badge-clean">Go</span>
                <span class="badge badge-fixed">Rust</span>
                <span class="badge badge-clean">C++</span>
                <span class="badge badge-fixed">Java</span>
                <span class="badge badge-clean">YAML</span>
                <span class="badge badge-fixed">HTML</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ==========================================================
    #  🚀 RESCUE EXECUTION
    # ==========================================================

    # --- Validate path ---
    if not config['path']:
        st.error("❌ Please enter a project path in the sidebar.")
        return

    root_path = Path(config['path'])
    if not root_path.exists():
        st.error(f"❌ Path not found: `{root_path}`")
        return

    # --- Validate API key for cloud providers ---
    if config['provider'] != "ollama" and not config['key']:
        st.error(f"❌ API key required for **{config['provider'].capitalize()}**. Enter it in the sidebar.")
        return

    # --- Discover files ---
    files = scan_files(root_path)
    if not files:
        st.warning("⚠️ No scannable files found in the target path.")
        return

    # --- Build args namespace for AIProvider ---
    args = SimpleNamespace(
        provider=config['provider'],
        key=config['key'] if config['key'] else None,
        model=config['model'],
        url=config['url'],
    )
    ai = AIProvider(args)

    # --- Setup directories ---
    if not config['dry_run']:
        BACKUP_DIR.mkdir(exist_ok=True)
        FIXED_DIR.mkdir(exist_ok=True)

    # --- Show scan info ---
    st.markdown(f"""
    <div class="scan-status">
        <div class="pulse"></div>
        <span>Scanning <strong>{len(files)}</strong> files with <strong>{config['provider'].upper()}</strong>
        ({ai.model}) {'🔒 DRY-RUN' if config['dry_run'] else ''}</span>
    </div>
    """, unsafe_allow_html=True)

    progress_bar = st.progress(0, text="Initializing scan...")
    status_area = st.empty()

    stats = {'passed': 0, 'failed': 0, 'skipped': 0}
    logs = []
    original_codes = {}
    fixed_codes = {}

    executor = Executor()

    for idx, f_path in enumerate(files):
        fname = f_path.name
        progress = (idx + 1) / len(files)
        progress_bar.progress(progress, text=f"Scanning {fname} ({idx+1}/{len(files)})")

        entry = {'file': fname, 'status': 'FIXED', 'error': ''}

        # Read original code for display
        try:
            with open(f_path, 'r', encoding='utf-8', errors='ignore') as fl:
                original_codes[fname] = fl.read()
        except Exception:
            original_codes[fname] = ""

        fixed = False
        current_code_path = f_path

        # --- RETRY LOOP (Run -> Fail -> Fix -> Retry) ---
        for i in range(1, 4):
            res = executor.run(current_code_path)

            # SKIPPED
            if "SKIPPED" in res.stderr:
                entry['status'] = "SKIPPED"
                entry['error'] = res.stderr
                stats['skipped'] += 1
                fixed = True
                break

            # SUCCESS
            if res.returncode == 0:
                entry['status'] = "FIXED" if i > 1 else "CLEAN"
                stats['passed'] += 1
                fixed = True
                break

            # FAILURE — ATTEMPT REPAIR
            entry['error'] = res.stderr.strip() or res.stdout.strip()

            if not config['dry_run']:
                try:
                    # 1. Backup on first failure
                    if i == 1:
                        shutil.copy2(f_path, BACKUP_DIR / f"{fname}.bak")

                    # 2. Read broken code
                    with open(current_code_path, 'r', encoding='utf-8', errors='ignore') as fl:
                        broken_code = fl.read()

                    # 3. AI Fix
                    status_area.markdown(f"""
                    <div class="scan-status">
                        <div class="pulse"></div>
                        <span>🧠 AI repairing <strong>{fname}</strong> (attempt {i}/3)...</span>
                    </div>
                    """, unsafe_allow_html=True)

                    fix_raw = ai.query(get_prompt(broken_code, entry['error']))
                    fixed_code = clean(fix_raw)

                    # 4. Save to FIXED_DIR
                    save_path = FIXED_DIR / fname
                    if len(fixed_code) > 10:
                        with open(save_path, 'w', encoding='utf-8') as fl:
                            fl.write(fixed_code)
                        current_code_path = save_path
                        fixed_codes[fname] = fixed_code
                    else:
                        break  # AI returned empty response

                except Exception as e:
                    entry['error'] = f"Repair Failed: {e}"
                    break

        if not fixed:
            entry['status'] = "FAILED"
            stats['failed'] += 1

        logs.append(entry)

        # Live update status
        status_area.markdown(f"""
        <div class="scan-status">
            <div class="pulse"></div>
            <span>{'✅' if fixed else '❌'} {fname} — <strong>{entry['status']}</strong></span>
        </div>
        """, unsafe_allow_html=True)

    # --- Scan Complete ---
    progress_bar.progress(1.0, text="✅ Scan Complete!")

    # Generate HTML report
    report_path = generate_report(stats, logs, os.path.abspath(FIXED_DIR))

    # Save to session state
    st.session_state.scan_complete = True
    st.session_state.stats = stats
    st.session_state.logs = logs
    st.session_state.original_codes = original_codes
    st.session_state.fixed_codes = fixed_codes

    # Clear status
    status_area.empty()
    time.sleep(0.3)

    # --- Render results ---
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 1.5rem; border-color: rgba(106,153,85,0.3);">
        <p style="font-size: 1.5rem; margin: 0;">✅ Rescue Complete!</p>
        <p style="color: #8b949e; font-size: 0.88rem; margin: 0.3rem 0 0;">
            All files have been scanned and processed.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    render_metrics(stats)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_results_table(logs)
    render_file_details(logs, original_codes, fixed_codes)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_downloads()


if __name__ == "__main__":
    main()
