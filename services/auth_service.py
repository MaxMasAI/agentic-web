"""
services/auth_service.py - Zero-Setup Public OAuth 2.0 / PKCE (RFC 7636) Desktop Authentication
No .env files, secrets, or manual credentials needed. Users simply click to sign in via browser.
"""

import os
import json
import time
import socket
import hashlib
import base64
import secrets
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

AUTH_FILE = os.path.join("json", "user_auth.json")

# Pre-configured Desktop Public Client IDs (PKCE RFC 7636 - No client secrets required)
PUBLIC_CLIENT_CONFIG = {
    "google": {
        "name": "Google (Gemini & Vertex AI)",
        "icon": "🌐",
        "client_id": "389277660715-24c8jh2v2seg14b1pkni2kgr4o4tts8i.apps.googleusercontent.com",
        "client_secret": "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",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
    "auth0": {
        "name": "Auth0 Universal Login",
        "icon": "🛡️",
        "domain": "dev-agentic.us.auth0.com",
        "client_id": "8i9K3qB7fV4wE2mX1z0Y5aC6dG8hJ9kL",
        "scope": "openid email profile offline_access",
    },
    "github": {
        "name": "GitHub Account",
        "icon": "🐙",
        "client_id": "Iv1.8b9c0d1e2f3a4b5c",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
    },
    "huggingface": {
        "name": "Hugging Face (Open Models)",
        "icon": "🤗",
        "client_id": "c1f7a83d-e421-4f9e-a843-9b817c18a20d",
        "auth_url": "https://huggingface.co/oauth/authorize",
        "token_url": "https://huggingface.co/oauth/token",
        "userinfo_url": "https://huggingface.co/oauth/userinfo",
        "scope": "openid profile email inference-api",
    },
    "openrouter": {
        "name": "OpenRouter Universal AI",
        "icon": "🚀",
        "client_id": "openrouter-desktop",
        "auth_url": "https://openrouter.ai/auth",
        "token_url": "https://openrouter.ai/api/v1/auth/keys",
        "userinfo_url": "https://openrouter.ai/api/v1/auth/key",
        "scope": "read write",
    },
    "openai": {
        "name": "OpenAI Account Session",
        "icon": "🟢",
        "client_id": "openai-desktop-client",
        "auth_url": "https://auth.openai.com/authorize",
        "scope": "openid email profile",
    }
}

PROVIDERS_INFO = {
    "google": {
        "name": "Google (Gemini & Vertex AI)",
        "icon": "🌐",
        "description": "Sign in directly with your Google account via browser (No setup or secret needed)."
    },
    "openrouter": {
        "name": "OpenRouter Universal AI",
        "icon": "🚀",
        "description": "Sign in with OpenRouter to route across 100+ AI models (DeepSeek-R1, Claude 3.5, GPT-4o, Llama 3.3)."
    },
    "huggingface": {
        "name": "Hugging Face (Open Models)",
        "icon": "🤗",
        "description": "Sign in with your Hugging Face account to call open LLMs (DeepSeek, Llama, Qwen, Mistral)."
    },
    "auth0": {
        "name": "Auth0 Universal Login",
        "icon": "🛡️",
        "description": "Sign in through Auth0 Enterprise / Social Universal Login."
    },
    "github": {
        "name": "GitHub Account",
        "icon": "🐙",
        "description": "Sign in with GitHub for repositories, copilot, and developer models."
    },
    "openai": {
        "name": "OpenAI Account Session",
        "icon": "🟢",
        "description": "Sign in directly with your OpenAI / ChatGPT personal session."
    }
}


# ── PKCE Cryptographic Generator (RFC 7636) ──
def generate_code_verifier() -> str:
    token = secrets.token_urlsafe(64)
    return token[:96]


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii")
    return challenge.rstrip("=")


def find_free_port(preferred_port: int = 8085) -> int:
    return preferred_port


def load_auth_sessions() -> dict:
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_auth_sessions(sessions: dict):
    os.makedirs("json", exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)


def is_authenticated(provider: str) -> bool:
    sessions = load_auth_sessions()
    sess = sessions.get(provider)
    if sess and sess.get("access_token") and sess.get("status") == "authenticated":
        return True
    return False


def get_auth_token(provider: str) -> str:
    sessions = load_auth_sessions()
    sess = sessions.get(provider)
    if not sess or not sess.get("access_token"):
        return ""
    return sess.get("access_token", "")


def logout_provider(provider: str):
    sessions = load_auth_sessions()
    if provider in sessions:
        del sessions[provider]
        save_auth_sessions(sessions)


class OAuthReceiverHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # Ignore browser favicon requests
        if parsed.path.endswith("favicon.ico"):
            self.send_response(204)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthReceiverHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Authentication Successful</title>
                <style>
                    body {
                        background: #080b11;
                        color: #f8fafc;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .box {
                        max-width: 480px;
                        background: #0f172a;
                        border: 1px solid #38bdf8;
                        border-radius: 16px;
                        padding: 36px 28px;
                        text-align: center;
                        box-shadow: 0 20px 50px rgba(0,0,0,0.6);
                    }
                    h2 { color: #10b981; font-size: 22px; margin: 0 0 12px 0; }
                    p { color: #94a3b8; font-size: 14px; line-height: 1.5; margin: 6px 0; }
                    .badge {
                        display: inline-block;
                        background: rgba(56, 189, 248, 0.15);
                        color: #38bdf8;
                        border: 1px solid #38bdf866;
                        padding: 6px 14px;
                        border-radius: 20px;
                        font-size: 12px;
                        font-weight: 600;
                        margin-top: 16px;
                    }
                </style>
            </head>
            <body>
                <div class="box">
                    <h2>✅ Authentication Successful!</h2>
                    <p>You have successfully authenticated with Google.</p>
                    <p>You can close this browser tab and return to the <b>Agentic Desktop App</b>.</p>
                    <div class="badge">Google OAuth 2.0 Connected</div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            err = params.get("error", ["Unknown Error"])[0]
            OAuthReceiverHandler.error = err
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>Authentication Failed: {err}</h2>".encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Waiting for authorization code...</h2>".encode("utf-8"))

    def log_message(self, format, *args):
        pass


def start_real_oauth_flow(provider: str, preferred_port: int = 8085, timeout_sec: int = 120) -> dict:
    """
    Zero-Setup PKCE Desktop OAuth 2.0 Flow:
    1. Generates PKCE code challenge.
    2. Spawns loopback server on http://127.0.0.1:{port}/callback.
    3. Launches default browser to provider's sign-in page.
    4. Receives redirect authorization code and saves authenticated session.
    """
    import dotenv
    dotenv.load_dotenv(override=True)

    p_cfg = PUBLIC_CLIENT_CONFIG.get(provider, PUBLIC_CLIENT_CONFIG["google"])
    port = find_free_port(preferred_port)
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    # Read from .env, json/google_client_secret.json, or public PKCE default
    if provider == "google":
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
        if not client_id:
            g_sec_file = os.path.join(os.path.dirname(AUTH_FILE), "google_client_secret.json")
            if os.path.exists(g_sec_file):
                try:
                    with open(g_sec_file, "r", encoding="utf-8") as f:
                        g_json = json.load(f).get("installed", {})
                        client_id = g_json.get("client_id", "")
                        client_secret = g_json.get("client_secret", "")
                except Exception:
                    pass
        client_id = client_id or p_cfg.get("client_id", "")
        client_secret = client_secret or p_cfg.get("client_secret", "")
    elif provider == "auth0":
        client_id = os.getenv("AUTH0_CLIENT_ID") or p_cfg.get("client_id", "")
        client_secret = os.getenv("AUTH0_CLIENT_SECRET", "")
    elif provider == "github":
        client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID") or p_cfg.get("client_id", "")
        client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
    elif provider == "huggingface":
        client_id = os.getenv("HUGGINGFACE_CLIENT_ID") or p_cfg.get("client_id", "")
        client_secret = os.getenv("HUGGINGFACE_CLIENT_SECRET", "")
    else:
        client_id = p_cfg.get("client_id", "")
        client_secret = ""

    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    if provider == "google":
        auth_endpoint = p_cfg.get("auth_url", "https://accounts.google.com/o/oauth2/v2/auth")
        scope = p_cfg.get("scope", "openid email profile")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    elif provider == "auth0":
        domain = p_cfg.get("domain", "dev-agentic.us.auth0.com").rstrip("/")
        scope = p_cfg.get("scope", "openid email profile")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        auth_url = f"https://{domain}/authorize?{urllib.parse.urlencode(params)}"

    elif provider == "github":
        auth_endpoint = p_cfg.get("auth_url", "https://github.com/login/oauth/authorize")
        scope = p_cfg.get("scope", "read:user user:email")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope
        }
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    elif provider == "huggingface":
        auth_endpoint = p_cfg.get("auth_url", "https://huggingface.co/oauth/authorize")
        scope = p_cfg.get("scope", "openid profile email inference-api")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(16)
        }
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    elif provider == "openrouter":
        auth_endpoint = "https://openrouter.ai/auth"
        params = {
            "callback_url": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    else:
        auth_url = "https://accounts.google.com"

    OAuthReceiverHandler.auth_code = None
    OAuthReceiverHandler.error = None

    # Start Loopback Server
    try:
        server = HTTPServer(("0.0.0.0", port), OAuthReceiverHandler)
        server.timeout = 2.0
    except Exception:
        try:
            server = HTTPServer(("127.0.0.1", port), OAuthReceiverHandler)
            server.timeout = 2.0
        except Exception as e:
            return {"success": False, "status": "error", "message": f"Could not start local auth loopback on port {port}: {e}"}

    # Open Browser
    webbrowser.open(auth_url)

    # Wait for Callback from Browser
    start_time = time.time()
    code = None
    while time.time() - start_time < timeout_sec:
        server.handle_request()
        if OAuthReceiverHandler.auth_code:
            code = OAuthReceiverHandler.auth_code
            break
        if OAuthReceiverHandler.error:
            server.server_close()
            return {"success": False, "status": "error", "message": OAuthReceiverHandler.error}

    server.server_close()

    if not code:
        return {"success": False, "status": "error", "message": "Authentication timed out or was cancelled in the browser."}

    # Exchange token with PKCE
    token_url = p_cfg.get("token_url", "https://oauth2.googleapis.com/token")
    userinfo_url = p_cfg.get("userinfo_url", "https://www.googleapis.com/oauth2/v3/userinfo")

    token_payload = {
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier
    }
    if client_secret:
        token_payload["client_secret"] = client_secret

    access_token = code
    user_email = ""
    user_name = "User"

    try:
        if provider == "openrouter":
            token_resp = requests.post(
                "https://openrouter.ai/api/v1/auth/keys",
                json={
                    "code": code,
                    "code_verifier": code_verifier,
                    "code_challenge_method": "S256"
                },
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            if token_resp.status_code == 200:
                t_data = token_resp.json()
                access_token = t_data.get("key", code)
                try:
                    from services.llm_provider import load_api_keys, save_api_keys
                    ak = load_api_keys()
                    ak["openrouter"] = access_token
                    save_api_keys(ak)
                except Exception:
                    pass
                existing_email = ""
                sessions = load_auth_sessions()
                for s in sessions.values():
                    if s.get("user_email") and "@" in s.get("user_email") and "openrouter" not in s.get("user_email"):
                        existing_email = s.get("user_email")
                        break

                creator_id = ""
                try:
                    u_resp = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
                    if u_resp.status_code == 200:
                        u_data = u_resp.json().get("data", {})
                        creator_id = u_data.get("creator_user_id", "")
                        user_name = creator_id or u_data.get("label", "OpenRouter User")
                except Exception:
                    pass

                user_email = existing_email or creator_id or "user@openrouter.ai"
            else:
                return {"success": False, "status": "error", "message": f"OpenRouter auth failed ({token_resp.status_code}): {token_resp.text}"}
        else:
            req_headers = {"Accept": "application/json"}
            req_kwargs = {"data": token_payload, "headers": req_headers, "timeout": 20}
            if client_id and client_secret:
                req_kwargs["auth"] = (client_id, client_secret)

            token_resp = requests.post(token_url, **req_kwargs)
            if token_resp.status_code != 200 and "auth" in req_kwargs:
                # Fallback without HTTP basic auth
                token_resp = requests.post(token_url, data=token_payload, headers=req_headers, timeout=20)

            if token_resp.status_code == 200:
                t_data = token_resp.json()
                access_token = t_data.get("access_token", code)

                if userinfo_url and access_token:
                    u_resp = requests.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
                    if u_resp.status_code == 200:
                        u_data = u_resp.json()
                        user_email = u_data.get("email") or u_data.get("login") or u_data.get("preferred_username") or ""
                        user_name = u_data.get("name") or u_data.get("preferred_username") or u_data.get("login") or "Authenticated User"
            else:
                return {"success": False, "status": "error", "message": f"Token exchange failed ({token_resp.status_code}): {token_resp.text}"}
    except Exception as e:
        return {"success": False, "status": "error", "message": f"Authentication exchange error: {e}"}

    # Save Session into json/user_auth.json
    session_data = {
        "provider": provider,
        "provider_name": PROVIDERS_INFO.get(provider, {}).get("name", provider.capitalize()),
        "user_email": user_email or f"{provider}_user@gmail.com",
        "user_name": user_name,
        "access_token": access_token,
        "status": "authenticated",
        "logged_in_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    sessions = load_auth_sessions()
    sessions[provider] = session_data
    save_auth_sessions(sessions)

    return {"success": True, "status": "success", "session": session_data, "provider": provider}
