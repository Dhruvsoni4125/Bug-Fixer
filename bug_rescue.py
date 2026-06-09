#!/usr/bin/env python3
"""
🐞 BUGRESCUE V2.0: WINDOWS REINFORCED EDITION
Autonomous Code Repair with Multi-Cloud Support & Windows Compatibility.
"""
import subprocess, sys, os, re, requests, argparse, shutil, html, time
from datetime import datetime
from pathlib import Path

# --- CONSOLE ENCODING FOR WINDOWS ---
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- AUTO-INSTALL DEPENDENCIES ---
def install_deps():
    try:
        import tqdm, colorama
    except ImportError:
        pass
try:
    from tqdm import tqdm
    from colorama import Fore, Back, Style, init
except ImportError:
    print("⚠️  Dependencies missing. Run: pip install -r requirements.txt")
    sys.exit(1)

# CONFIG & CONSTANTS
VERSION = "v2.0.0-WinReinforced"
BACKUP_DIR = Path(".bugrescue_backups")
FIXED_DIR = Path("fixed_code")
REPORT_FILE = "bugrescue_report.html"

# Initialize Colors
init(autoreset=True)

# --- AI PROVIDER LOGIC (WITH RETRY) ---
class AIProvider:
    def __init__(self, args):
        self.provider = args.provider
        self.key = args.key or os.getenv(f"{args.provider.upper()}_API_KEY")
        self.model = args.model
        self.url = args.url

        # Smart Defaults
        if self.provider == "ollama":
            self.url = self.url or "http://localhost:11434/api/generate"
            self.model = self.model or "qwen2.5-coder:14b"
        elif self.provider == "openai":
            self.url = "https://api.openai.com/v1/chat/completions"
            self.model = self.model or "gpt-4o"
        elif self.provider == "anthropic":
            self.url = "https://api.anthropic.com/v1/messages"
            self.model = self.model or "claude-3-5-sonnet-20240620"
        elif self.provider == "gemini":
            self.model = self.model or "gemini-1.5-pro"
            self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def query(self, prompt, retries=3):
        for attempt in range(retries):
            try:
                if self.provider == "ollama":
                    res = requests.post(self.url, json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}, timeout=120)
                    res.raise_for_status()
                    return res.json().get('response', '')

                elif self.provider == "openai":
                    if not self.key: return "ERROR: Missing OpenAI API Key."
                    headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "system", "content": "You are a Senior Engineer."}, {"role": "user", "content": prompt}],
                        "temperature": 0.2
                    }
                    res = requests.post(self.url, headers=headers, json=payload, timeout=60)
                    res.raise_for_status()
                    return res.json()['choices'][0]['message']['content']

                elif self.provider == "anthropic":
                    if not self.key: return "ERROR: Missing Anthropic API Key."
                    headers = {"x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
                    payload = {
                        "model": self.model,
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    res = requests.post(self.url, headers=headers, json=payload, timeout=60)
                    res.raise_for_status()
                    return res.json()['content'][0]['text']

                elif self.provider == "gemini":
                    if not self.key: return "ERROR: Missing Gemini API Key."
                    url = f"{self.url}?key={self.key}"
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    headers = {"Content-Type": "application/json"}
                    res = requests.post(url, headers=headers, json=payload, timeout=60)
                    res.raise_for_status()
                    res_json = res.json()
                    if 'candidates' in res_json and len(res_json['candidates']) > 0:
                        cand = res_json['candidates'][0]
                        if 'content' in cand and 'parts' in cand['content'] and len(cand['content']['parts']) > 0:
                            return cand['content']['parts'][0]['text']
                    return f"API ERROR: Unexpected Gemini response structure: {res_json}"

            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt) # Exponential backoff
                    continue
                return f"API ERROR: {str(e)}"
        return "ERROR: Max retries exceeded."

# --- CORE UTILS ---
def print_banner(provider, model):
    banner = rf"""
    {Fore.CYAN}
      ____              ____                           
     |  _ \            |  _ \                          
     | |_) |_   _  __ _| |_) |___  ___  ___ _   _  ___ 
     |  _ <| | | |/ _` |  _ <| _ \/ __|/ __| | | |/ _ \
     | |_) | |_| | (_| | |_) |  __/\__ \ (__| |_| |  __/
     |____/ \__,_|\__, |____/ \___||___/\___|\__,_|\___|
                   __/ |                                
    {Fore.WHITE}  Autonomous Repair Agent | {VERSION}
    {Fore.YELLOW}  ⚡ Engine: {provider.upper()} ({model})
    {Style.RESET_ALL}"""
    print(banner)

def generate_report(stats, logs, fixed_dir_abs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    css = "body{font-family:'Segoe UI',sans-serif;background:#1e1e1e;color:#d4d4d4;padding:20px;max-width:1000px;margin:0 auto} h1{color:#4ec9b0;border-bottom:1px solid #3c3c3c} .card{background:#252526;border:1px solid #3c3c3c;padding:15px;margin-bottom:20px;border-radius:6px} table{width:100%;border-collapse:collapse} th,td{padding:10px;border-bottom:1px solid #3c3c3c;text-align:left} .success{color:#6a9955} .fail{color:#f44747} .warn{color:#cca700} .info{color:#569cd6}"
    rows = "".join([f"<tr><td>{e['file']}</td><td class='{'success' if e['status'] in ('FIXED', 'CLEAN') else 'fail' if 'FAILED' in e['status'] else 'warn'}'><strong>{e['status']}</strong></td><td>{html.escape(e['error'])[:120]}</td></tr>" for e in logs])
    
    html_c = f"""
    <html><head><title>BugRescue Report</title><style>{css}</style></head><body>
    <h1>🐞 BugRescue Audit Report</h1>
    <div class='card' style='display:flex;gap:20px;text-align:center'>
        <div style='flex:1'><h2 class='success'>{stats['passed']}</h2>Fixed</div>
        <div style='flex:1'><h2 class='fail'>{stats['failed']}</h2>Failed</div>
        <div style='flex:1'><h2 class='warn'>{stats['skipped']}</h2>Skipped</div>
    </div>
    <div class='card'>
        <h3>📁 Output Location</h3>
        <p>Fixed files are saved in: <br><code class='info'>{fixed_dir_abs}</code></p>
    </div>
    <div class='card'><h3>Audit Log ({timestamp})</h3><table><tr><th>File</th><th>Status</th><th>Detection</th></tr>{rows}</table></div></body></html>
    """
    with open(REPORT_FILE, "w", encoding='utf-8') as f: f.write(html_c)
    return os.path.abspath(REPORT_FILE)

class Executor:
    def run(self, f_path):
        f = str(f_path) # Convert Path object to string
        ext = f_path.suffix.lower()
        cmd = []
        
        # --- WINDOWS COMPATIBILITY CHECK ---
        # We check if compilers exist using shutil.which() to avoid FileNotFoundError
        
        if ext == '.py': 
            cmd = [sys.executable, "-u", f] # Use current Python interpreter
        elif ext == '.js': 
            if shutil.which("node"): cmd = ["node", f]
            else: return subprocess.CompletedProcess([], 1, "", "SKIPPED: 'node' not found in PATH")
        elif ext == '.go': 
            if shutil.which("go"): cmd = ["go", "run", f]
            else: return subprocess.CompletedProcess([], 1, "", "SKIPPED: 'go' not found in PATH")
        elif ext == '.rs':
            if shutil.which("rustc"):
                bin_file = f_path.with_suffix('.exe' if os.name == 'nt' else '')
                # Compile first
                compile_res = subprocess.run(["rustc", f, "-o", str(bin_file)], capture_output=True, text=True)
                if compile_res.returncode != 0:
                    return subprocess.CompletedProcess([], 1, "", f"Rust Compile Failed:\n{compile_res.stderr}")
                cmd = [str(bin_file)]
            else: return subprocess.CompletedProcess([], 1, "", "SKIPPED: 'rustc' not found in PATH")
        elif ext == '.cpp':
            if shutil.which("g++"):
                bin_file = f_path.with_suffix('.exe' if os.name == 'nt' else '')
                compile_res = subprocess.run(["g++", f, "-o", str(bin_file)], capture_output=True, text=True)
                if compile_res.returncode != 0:
                    return subprocess.CompletedProcess([], 1, "", f"C++ Compile Failed:\n{compile_res.stderr}")
                cmd = [str(bin_file)]
            else: return subprocess.CompletedProcess([], 1, "", "SKIPPED: 'g++' not found in PATH")
        
        elif ext in ['.yaml', '.dockerfile', '.html']: 
            try:
                with open(f, 'r', encoding='utf-8') as fl: c = fl.read()
                if "password:" in c and "Secret" in c: return subprocess.CompletedProcess([], 1, "", "Hardcoded Secret Detected")
                return subprocess.CompletedProcess([], 0, "Valid", "")
            except Exception as e:
                return subprocess.CompletedProcess([], 1, "", f"Read Error: {e}")

        if not cmd: return subprocess.CompletedProcess([], 0, "", "SKIPPED: Unsupported File Type")
        
        try: 
            return subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired: 
            return subprocess.CompletedProcess([], 124, "", "TIMEOUT: Process took too long")
        except FileNotFoundError:
             return subprocess.CompletedProcess([], 1, "", "CRITICAL: Compiler executable missing from system")
        except Exception as e:
             return subprocess.CompletedProcess([], 1, "", f"SYSTEM ERROR: {e}")

def get_prompt(code, error):
    return f"Act as a Principal Engineer. Fix this code.\nERROR: {error[-2000:]}\nCODE: {code}\nINSTRUCTION: Return ONLY the fixed code block inside markdown code fences. No explanations."

def clean(raw):
    # ROBUST CLEANER: Regex extracts content inside ``` code blocks
    pattern = r"```(?:\w+)?\s*(.*?)```"
    match = re.search(pattern, raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip() # Fallback if no markdown found

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("path", help="Project path to scan")
    parser.add_argument("--dry-run", action="store_true", help="Audit only (no changes)")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "openai", "anthropic", "gemini"], help="AI Provider")
    parser.add_argument("--key", help="API Key for cloud providers")
    parser.add_argument("--model", help="Override default model")
    parser.add_argument("--url", help="Override Ollama URL")
    args = parser.parse_args()

    # --- SETUP PATHS ---
    root_path = Path(args.path)
    if not root_path.exists():
        print(f"{Fore.RED}❌ Path not found: {root_path}{Style.RESET_ALL}")
        return

    ai = AIProvider(args)
    print_banner(ai.provider, ai.model)
    
    # --- FILE SCANNING (MOVED AFTER ARGS) ---
    files = []
    ignore_dirs = {BACKUP_DIR.name, FIXED_DIR.name, ".git", "__pycache__", "node_modules"}
    
    if root_path.is_file():
        if root_path.suffix.lower() in ('.py','.js','.go','.rs','.cpp','.java','.yaml','.dockerfile','.html'):
            files.append(root_path)
    else:
        for r, dirs, fs in os.walk(root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for f in fs:
                if f.lower().endswith(('.py','.js','.go','.rs','.cpp','.java','.yaml','.dockerfile','.html')):
                    files.append(Path(r) / f)
    
    if not files:
        print(f"{Fore.RED}❌ No scannable files found.{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}🚀 Launching on {len(files)} Artifacts...{Style.RESET_ALL}")
    
    # Create Output Directories
    if not args.dry_run:
        BACKUP_DIR.mkdir(exist_ok=True)
        FIXED_DIR.mkdir(exist_ok=True)
    
    stats = {'passed': 0, 'failed': 0, 'skipped': 0}
    logs = []
    
    pbar = tqdm(files, unit="file", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}")
    
    executor = Executor()

    for f_path in pbar:
        fname = f_path.name
        pbar.set_description(f"Scanning {fname}")
        entry = {'file': fname, 'status': 'FIXED', 'error': ''}
        
        fixed = False
        current_code_path = f_path

        # RETRY LOOP (Run -> Fail -> Fix -> Retry)
        for i in range(1, 4):
            res = executor.run(current_code_path)
            
            # Handle SKIPPED (Missing compiler, etc)
            if "SKIPPED" in res.stderr:
                entry['status'] = "SKIPPED"
                entry['error'] = res.stderr
                stats['skipped'] += 1
                fixed = True # Not really fixed, but handled
                break

            # SUCCESS
            if res.returncode == 0:
                entry['status'] = "FIXED" if i > 1 else "CLEAN"
                stats['passed'] += 1
                fixed = True
                break
            
            # FAILURE - ATTEMPT REPAIR
            entry['error'] = res.stderr.strip() or res.stdout.strip()
            
            if not args.dry_run:
                try:
                    # 1. Backup original on first failure
                    if i == 1:
                        shutil.copy2(f_path, BACKUP_DIR / f"{fname}.bak")
                    
                    # 2. Read broken code
                    with open(current_code_path, 'r', encoding='utf-8', errors='ignore') as fl: 
                        broken_code = fl.read()
                    
                    # 3. Get AI Fix
                    fix_raw = ai.query(get_prompt(broken_code, entry['error']))
                    fixed_code = clean(fix_raw)
                    
                    # 4. Save to FIXED_DIR (Safety First)
                    # We maintain relative structure inside fixed_code/ if possible, or just flat for now
                    save_path = FIXED_DIR / fname
                    
                    if len(fixed_code) > 10:
                        with open(save_path, 'w', encoding='utf-8') as fl: 
                            fl.write(fixed_code)
                        # Point next iteration to the FIXED file to verify if it passes
                        current_code_path = save_path
                    else:
                        break # AI returned empty/bad response

                except Exception as e:
                    entry['error'] = f"Repair Failed: {e}"
                    break
        
        if not fixed:
            entry['status'] = "FAILED"
            stats['failed'] += 1
            tqdm.write(f"{Fore.RED}✘ Failed: {fname}{Style.RESET_ALL}")
        
        logs.append(entry)

    report_path = generate_report(stats, logs, os.path.abspath(FIXED_DIR))
    print(f"\n{Fore.GREEN}✔ Rescue Complete!{Style.RESET_ALL}")
    print(f"📊 Report: {Fore.BLUE}{report_path}{Style.RESET_ALL}")
    print(f"📁 Fixed Files: {Fore.BLUE}{os.path.abspath(FIXED_DIR)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
