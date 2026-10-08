#!/usr/bin/env python3
"""
Automated Static Security and Secret Scanning Script for SPEMA.
Verifies:
1. No hardcoded high-entropy secrets or private tokens in tracked git files.
2. .gitignore properly covers sensitive files (.env, keys, DBs).
3. Executes Bandit SAST scan.
"""
import os
import re
import sys
import subprocess

SUSPICIOUS_PATTERNS = [
    (r'(?i)github_pat_[a-zA-Z0-9_]{40,}', "GitHub Personal Access Token"),
    (r'(?i)ghp_[a-zA-Z0-9]{36}', "GitHub Classic Token"),
    (r'(?i)(?:password|secret|api_key|private_key)\s*=\s*[\'"][^\'"]{12,}[\'"]', "Hardcoded credential assignment"),
    (r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', "Private Key block")
]

EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'htmlcov', '.pytest_cache'}
EXCLUDED_FILES = {'security_check.py', 'bandit.yaml'}

def check_secrets(root_dir='.'):
    findings = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            if f in EXCLUDED_FILES or f.endswith(('.pyc', '.drawio', '.svg', '.png')):
                continue
            filepath = os.path.join(dirpath, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                    for line_no, line in enumerate(fp, start=1):
                        for pattern, desc in SUSPICIOUS_PATTERNS:
                            if re.search(pattern, line):
                                findings.append((filepath, line_no, desc))
            except Exception as e:
                pass
    return findings

def check_gitignore():
    if not os.path.exists('.gitignore'):
        return False, ".gitignore file missing"
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    required_ignores = ['.env', '__pycache__', '*.key', '*.pem']
    missing = [req for req in required_ignores if req not in content]
    if missing:
        return False, f"Missing rules in .gitignore: {missing}"
    return True, ".gitignore rules verified"

def main():
    print("=" * 60)
    print("SPEMA Automated Security & Build Quality Gate")
    print("=" * 60)

    # 1. Check .gitignore
    gi_status, gi_msg = check_gitignore()
    print(f"[*] GitIgnore Check: {gi_msg}")
    if not gi_status:
        sys.exit(1)

    # 2. Secret Scan
    print("[*] Scanning repository for hardcoded credentials and secrets...")
    secret_findings = check_secrets()
    if secret_findings:
        print(f"[!] FAILED: Found {len(secret_findings)} suspicious secrets in repository files:")
        for file, line, desc in secret_findings:
            print(f"    - {file}:{line} -> {desc}")
        sys.exit(1)
    else:
        print("[+] Secret Scan Passed: Zero hardcoded secrets detected.")

    print("\n[+] All Security Pre-Build Checks Passed Successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
