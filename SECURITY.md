# 🛡️ Security Policy

> **Organization**: [MaxMasAI](https://github.com/MaxMasAI)  
> **Owner & Founder**: [Sahil Kumar Dhala](https://github.com/Sahilkumardhala)  
> **License**: [MIT License](LICENSE)  

The **MaxMasAI** security and core development team take the security and integrity of **Agentic Web** seriously. This document outlines our security policies, supported versions, sandboxing principles, credential governance, and responsible vulnerability reporting procedures.

---

## 📦 Supported Versions

We actively provide security patches and updates for the following versions:

| Version | Supported | Notes |
|---|---|---|
| **2.5.x** | ✅ Yes | Current active release branch. |
| **2.4.x** | ✅ Yes | Critical security and dependency fixes only. |
| **< 2.4.0** | ❌ No | End of Life (EOL). Please upgrade to latest. |

---

## 🔒 Security Architecture & Sandboxing

Agentic Web operates as an autonomous desktop environment executing AI models, browser interactions, and code interpreter scripts. The platform implements multi-layer defense mechanisms:

### 1. Credential Protection & Secret Governance
- **Local Key Storage**: API keys and OAuth tokens stored in `json/api_keys.json` and `json/user_auth.json` are isolated locally and never transmitted to external analytics or telemetry services.
- **Log Masking**: Sensitive tokens (OpenAI, Anthropic, Gemini, DeepSeek, OpenRouter) are automatically redacted from console outputs and log files in `logs/`.
- **PKCE OAuth 2.0**: Web-based provider authentications employ PKCE (Proof Key for Code Exchange) to prevent authorization code interception.

### 2. Code Execution Sandboxing (Playground Studio)
- **Subprocess Isolation**: Scripts executed in the Python Sandbox run in dedicated child processes with strict execution timeouts.
- **Path Traversal Protection**: File operations via the built-in File Explorer validate workspace boundaries to prevent directory traversal (`../`) attacks.
- **Dependency Whitelisting**: Automated package installations require explicit user confirmation before executing `pip install`.

### 3. Model Context Protocol (MCP) Safety
- **Schema Validation**: All incoming and outgoing tool parameters are validated against strict JSON schemas before invoking local or remote tools.
- **Read-Only Defaults**: External tools default to read-only execution modes unless write permissions are explicitly granted by the user in Settings.

### 4. Browser Automation & Privacy
- **Dedicated Browser Profiles**: Chrome automation via CDP runs in isolated temporary profiles or explicit user-designated spaces.
- **Cookie Sanitization**: Captured vision verification screenshots in `visuals/` avoid storing plaintext session cookies.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within Agentic Web, please report it responsibly:

### How to Report
1. **Do NOT open a public GitHub issue** for undisclosed security vulnerabilities.
2. Email the vulnerability report directly to:
   - **Owner**: [Sahil Kumar Dhala](https://github.com/Sahilkumardhala)
   - **Security Inbox**: `security@maxmasai.com` *(or via private GitHub Security Advisory)*
3. Alternatively, report via **GitHub Security Advisories** on the [MaxMasAI Repository](https://github.com/MaxMasAI).

### What to Include in Your Report
To help us triage and resolve the issue quickly, please include:
- **Type of Issue**: (e.g., Code Execution Escape, Insecure Credential Storage, Path Traversal, SSRF in MCP tool).
- **Affected Version**: (e.g., v2.5.0 on Windows/Linux/macOS).
- **Proof of Concept (PoC)**: Step-by-step reproduction instructions or test script.
- **Impact Assessment**: Potential risk to end users or sensitive environments.

### Response Timelines
- **Initial Acknowledgement**: Within **24 to 48 hours**.
- **Triage & Severity Assessment**: Within **3 to 5 business days**.
- **Fix & Patch Release**: Critical vulnerabilities are patched in a priority hotfix release.

---

## 🤝 Responsible Disclosure & Hall of Fame

We believe in collaborative, responsible disclosure:
- We ask security researchers to give us reasonable time to investigate and release a fix before public disclosure.
- Security researchers who follow responsible disclosure practices will be credited in our Release Notes and `CREDITS` section.

---

*© 2026 MaxMasAI. Owned & Maintained by [Sahilkumardhala](https://github.com/Sahilkumardhala). Released under the [MIT License](LICENSE).*
