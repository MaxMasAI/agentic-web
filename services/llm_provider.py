"""
services/llm_provider.py - Unified Multi-Model LLM Engine (Cloud & Local Ollama)
"""

import os
import json
import httpx
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEYS_FILE = os.path.join("json", "api_keys.json")

DEFAULT_MODELS = [
    # Google Gemini & Vertex AI (Active Production Models)
    {"id": "gemini-2.0-flash", "name": "✨ Google Gemini 2.0 Flash", "provider": "Google", "badge": "CLOUD"},
    {"id": "gemini-1.5-flash", "name": "✨ Google Gemini 1.5 Flash", "provider": "Google", "badge": "CLOUD"},
    {"id": "gemini-1.5-pro", "name": "✨ Google Gemini 1.5 Pro", "provider": "Google", "badge": "CLOUD"},
    # Hugging Face Open Models (Free Serverless Inference & OAuth)
    {"id": "hf:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "name": "🤗 DeepSeek R1 (Hugging Face)", "provider": "HuggingFace", "badge": "CLOUD"},
    {"id": "hf:Qwen/Qwen2.5-Coder-32B-Instruct", "name": "🤗 Qwen 2.5 Coder 32B (Hugging Face)", "provider": "HuggingFace", "badge": "CLOUD"},
    {"id": "hf:meta-llama/Llama-3.3-70B-Instruct", "name": "🤗 Llama 3.3 70B (Hugging Face)", "provider": "HuggingFace", "badge": "CLOUD"},
    {"id": "hf:mistralai/Mistral-7B-Instruct-v0.3", "name": "🤗 Mistral 7B (Hugging Face)", "provider": "HuggingFace", "badge": "CLOUD"},
    # OpenRouter Universal AI Models (100+ Cloud & Open LLMs)
    {"id": "openrouter:deepseek/deepseek-r1", "name": "🚀 DeepSeek R1 (OpenRouter)", "provider": "OpenRouter", "badge": "CLOUD"},
    {"id": "openrouter:deepseek/deepseek-chat", "name": "🚀 DeepSeek V3 (OpenRouter)", "provider": "OpenRouter", "badge": "CLOUD"},
    {"id": "openrouter:anthropic/claude-3.5-sonnet", "name": "🚀 Claude 3.5 Sonnet (OpenRouter)", "provider": "OpenRouter", "badge": "CLOUD"},
    {"id": "openrouter:openai/gpt-4o", "name": "🚀 OpenAI GPT-4o (OpenRouter)", "provider": "OpenRouter", "badge": "CLOUD"},
    {"id": "openrouter:meta-llama/llama-3.3-70b-instruct", "name": "🚀 Llama 3.3 70B (OpenRouter)", "provider": "OpenRouter", "badge": "CLOUD"},
    # OpenAI
    {"id": "gpt-4o", "name": "🟢 OpenAI GPT-4o", "provider": "OpenAI", "badge": "CLOUD"},
    {"id": "gpt-4o-mini", "name": "🟢 OpenAI GPT-4o Mini", "provider": "OpenAI", "badge": "CLOUD"},
    {"id": "o1-preview", "name": "🟢 OpenAI o1 Reasoning", "provider": "OpenAI", "badge": "CLOUD"},
    {"id": "o3-mini", "name": "🟢 OpenAI o3 Mini", "provider": "OpenAI", "badge": "CLOUD"},
    # Anthropic
    {"id": "claude-3-5-sonnet-20241022", "name": "🟣 Anthropic Claude 3.5 Sonnet", "provider": "Anthropic", "badge": "CLOUD"},
    # DeepSeek
    {"id": "deepseek-chat", "name": "🐋 DeepSeek V3 (Chat)", "provider": "DeepSeek", "badge": "CLOUD"},
    {"id": "deepseek-reasoner", "name": "🐋 DeepSeek R1 (Reasoner)", "provider": "DeepSeek", "badge": "CLOUD"},
    # Perplexity
    {"id": "sonar-pro", "name": "🔮 Perplexity Sonar Pro (Web)", "provider": "Perplexity", "badge": "CLOUD"},
    # xAI Grok
    {"id": "grok-2-latest", "name": "⚡ xAI Grok 2", "provider": "xAI", "badge": "CLOUD"},
]


def load_api_keys() -> dict:
    load_dotenv(override=True)
    keys = {
        "gemini": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "",
        "openrouter": os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY") or "",
        "huggingface": os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_TOKEN") or "",
        "openai": os.getenv("OPENAI_API_KEY") or "",
        "anthropic": os.getenv("ANTHROPIC_API_KEY") or "",
        "deepseek": os.getenv("DEEPSEEK_API_KEY") or "",
        "perplexity": os.getenv("PERPLEXITY_API_KEY") or "",
        "grok": os.getenv("GROK_API_KEY") or "",
        "ollama_url": os.getenv("OLLAMA_URL") or "http://localhost:11434",
    }
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    keys.update(saved)
        except Exception:
            pass
    return keys


def save_api_keys(keys_dict: dict):
    os.makedirs("json", exist_ok=True)
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys_dict, f, indent=2)


def is_provider_authenticated(provider: str, keys: dict) -> bool:
    """Checks if a provider has an active OAuth session or configured API key."""
    from services.auth_service import is_authenticated
    p = provider.lower()
    if "google" in p or "gemini" in p:
        return is_authenticated("google") or bool(keys.get("gemini"))
    elif "openrouter" in p:
        return is_authenticated("openrouter") or bool(keys.get("openrouter")) or bool(os.getenv("OPENROUTER_API_KEY"))
    elif "hugging" in p or "hf" in p:
        return is_authenticated("huggingface") or bool(keys.get("huggingface")) or bool(os.getenv("HF_TOKEN"))
    elif "openai" in p:
        return is_authenticated("openai") or bool(keys.get("openai"))
    elif "anthropic" in p or "claude" in p:
        return bool(keys.get("anthropic"))
    elif "deepseek" in p:
        return bool(keys.get("deepseek"))
    elif "perplexity" in p:
        return bool(keys.get("perplexity"))
    elif "xai" in p or "grok" in p:
        return bool(keys.get("grok"))
    elif "ollama" in p:
        return True
    return False


def get_available_models(only_authenticated: bool = True) -> list:
    """
    Returns list of models with logos, filtered strictly to only authenticated accounts/APIs.
    Discovers local Ollama models dynamically if Ollama is running.
    If no accounts/APIs are authenticated, returns an empty list.
    """
    keys = load_api_keys()
    models = []
    ollama_url = keys.get("ollama_url", "http://localhost:11434").rstrip("/")

    # Query Ollama for live local models
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=1.2)
        if resp.status_code == 200:
            data = resp.json()
            for m in data.get("models", []):
                m_name = m.get("name", "local-model")
                models.append({
                    "id": f"ollama:{m_name}",
                    "name": f"🦙 Ollama: {m_name}",
                    "provider": "Ollama (Local)",
                    "badge": "LOCAL"
                })
    except Exception:
        pass

    # Filter cloud models strictly by authentication status
    for m in DEFAULT_MODELS:
        if not only_authenticated or is_provider_authenticated(m["provider"], keys):
            models.append(m)

    return models


def generate_chat_response(
    messages: list,
    model_id: str = "gemini-2.0-flash",
    system_prompt: str = "",
    temperature: float = 0.7
) -> dict:
    """
    Unified chat generator supporting Gemini, Ollama, OpenAI, DeepSeek, Claude, and Perplexity.
    Returns: {"role": "assistant", "content": str, "model": str, "tokens": int}
    """
    # Apply System Prompt Extra plugin extensions
    try:
        from services.system_prompt_extra import get_system_prompt_extra_service
        system_prompt = get_system_prompt_extra_service().apply_to_prompt(system_prompt)
    except Exception:
        pass

    keys = load_api_keys()

    # 1. Local Ollama Model
    if model_id.startswith("ollama:"):
        actual_model = model_id.replace("ollama:", "")
        ollama_url = keys.get("ollama_url", "http://localhost:11434").rstrip("/")
        
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            ollama_messages.append({"role": m["role"], "content": m["content"]})

        try:
            resp = requests.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": actual_model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                },
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                return {
                    "role": "assistant",
                    "content": content,
                    "model": model_id,
                    "tokens": data.get("eval_count", len(content.split()))
                }
            else:
                return {
                    "role": "assistant",
                    "content": f"Ollama Error ({resp.status_code}): {resp.text}",
                    "model": model_id,
                    "tokens": 0
                }
        except Exception as e:
            return {
                "role": "assistant",
                "content": f"Could not connect to Ollama at {ollama_url}: {e}",
                "model": model_id,
                "tokens": 0
            }

    # 2. Google Gemini (Google API Key or Authenticated Google Account)
    from services.auth_service import is_authenticated, get_auth_token
    gemini_key = keys.get("gemini")
    oauth_token = get_auth_token("google") if is_authenticated("google") else ""

    if "gemini" in model_id.lower() or model_id.startswith("google:") or model_id.startswith("vertexai:"):
        # Format prompt history
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(f"System Instruction: {system_prompt}\n")
        for m in messages:
            prompt_parts.append(f"{m['role'].capitalize()}: {m['content']}")
        full_prompt = "\n\n".join(prompt_parts)

        # A. Try Google GenAI SDK (Vertex AI & Developer API)
        sdk_err = None
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "weighty-utility-419819"
        location = os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() in ("true", "1")

        # 1. Try GenAI SDK with OAuth Credentials for Vertex AI
        if oauth_token:
            try:
                from google.oauth2.credentials import Credentials as OAuthCreds
                from google import genai
                creds = OAuthCreds(token=oauth_token)
                client = genai.Client(vertexai=True, project=project_id, location=location, credentials=creds)
                for m_candidate in [model_id, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
                    clean_m = m_candidate.replace("google:", "").replace("vertexai:", "")
                    try:
                        resp = client.models.generate_content(
                            model=clean_m,
                            contents=full_prompt,
                        )
                        text = resp.text or ""
                        if text:
                            return {
                                "role": "assistant",
                                "content": text,
                                "model": clean_m,
                                "tokens": len(text.split())
                            }
                    except Exception as err:
                        sdk_err = f"Vertex AI (OAuth): {err}"
            except Exception as e:
                sdk_err = f"Vertex AI (OAuth Init): {e}"

        # 2. Try GenAI SDK with API Key
        if gemini_key:
            try:
                from google import genai
                if use_vertex:
                    client = genai.Client(vertexai=True, project=project_id, location=location, api_key=gemini_key)
                else:
                    client = genai.Client(api_key=gemini_key)
                for m_candidate in [model_id, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
                    clean_m = m_candidate.replace("google:", "").replace("vertexai:", "")
                    try:
                        resp = client.models.generate_content(
                            model=clean_m,
                            contents=full_prompt,
                        )
                        text = resp.text or ""
                        if text:
                            return {
                                "role": "assistant",
                                "content": text,
                                "model": clean_m,
                                "tokens": len(text.split())
                            }
                    except Exception as err:
                        # Fallback to standard studio client if vertex failed
                        if use_vertex:
                            try:
                                fallback_client = genai.Client(api_key=gemini_key)
                                resp2 = fallback_client.models.generate_content(model=clean_m, contents=full_prompt)
                                text2 = resp2.text or ""
                                if text2:
                                    return {
                                        "role": "assistant",
                                        "content": text2,
                                        "model": clean_m,
                                        "tokens": len(text2.split())
                                    }
                            except Exception:
                                pass
                        sdk_err = f"GenAI SDK (API Key): {err}"
            except Exception as e:
                sdk_err = f"GenAI SDK Init: {e}"

        # B. Try Google REST API with OAuth Bearer Token (Generative Language & Vertex AI)
        oauth_err = None
        if oauth_token:
            candidate_endpoints = []
            for m_candidate in [model_id, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
                clean_m = m_candidate.replace("google:", "").replace("vertexai:", "")
                # 1. Google Cloud Vertex AI Endpoint
                candidate_endpoints.append((
                    clean_m,
                    f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{clean_m}:generateContent",
                    {"contents": [{"role": "user", "parts": [{"text": full_prompt}]}]}
                ))
                # 2. Google AI Studio Generative Language Endpoint
                candidate_endpoints.append((
                    clean_m,
                    f"https://generativelanguage.googleapis.com/v1beta/models/{clean_m}:generateContent",
                    {"contents": [{"parts": [{"text": full_prompt}]}]}
                ))

            for m_candidate, url, payload in candidate_endpoints:
                try:
                    resp = requests.post(
                        url,
                        headers={"Authorization": f"Bearer {oauth_token}", "Content-Type": "application/json"},
                        json=payload,
                        timeout=30
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if text:
                                return {
                                    "role": "assistant",
                                    "content": text,
                                    "model": m_candidate,
                                    "tokens": len(text.split())
                                }
                    else:
                        oauth_err = f"Google API ({resp.status_code}): {resp.text}"
                except Exception as e:
                    oauth_err = str(e)

        # C. Return diagnostic info if live calls failed
        diag = []
        if sdk_err:
            diag.append(f"• **SDK Status**: {sdk_err}")
        if oauth_err:
            diag.append(f"• **OAuth Account**: {oauth_err}")

        diag_msg = "\n".join(diag) if diag else "Google API returned no response."

    # 3. Hugging Face Serverless Inference API (via InferenceClient)
    from services.auth_service import get_auth_token as get_hf_auth_token
    hf_token = get_hf_auth_token("huggingface") or keys.get("huggingface") or os.getenv("HF_TOKEN") or ""

    if model_id.startswith("hf:") or "huggingface" in model_id.lower() or (hf_token and any(k in model_id.lower() for k in ["llama", "qwen", "mistral", "deepseek"])):
        actual_hf_model = model_id.replace("hf:", "")
        # Map generic names to exact serverless endpoints
        if actual_hf_model == "deepseek-ai/DeepSeek-R1":
            actual_hf_model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

        api_msgs = []
        if system_prompt:
            api_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            api_msgs.append({"role": m["role"], "content": m["content"]})

        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token if hf_token else None)
            res = client.chat.completions.create(
                model=actual_hf_model,
                messages=api_msgs,
                max_tokens=2048,
                temperature=temperature
            )
            content = res.choices[0].message.content or ""
            if content:
                usage = res.usage.total_tokens if hasattr(res, "usage") and res.usage else len(content.split())
                return {"role": "assistant", "content": content, "model": model_id, "tokens": usage}
        except Exception as e:
            try:
                hf_router_url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
                headers = {"Content-Type": "application/json"}
                if hf_token:
                    headers["Authorization"] = f"Bearer {hf_token}"
                resp = requests.post(
                    hf_router_url,
                    headers=headers,
                    json={"model": actual_hf_model, "messages": api_msgs, "temperature": temperature, "max_tokens": 2048},
                    timeout=45
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {}).get("total_tokens", len(content.split()))
                    return {"role": "assistant", "content": content, "model": model_id, "tokens": usage}
            except Exception:
                pass
            return {"role": "assistant", "content": f"**[Hugging Face Error]** Could not query model `{actual_hf_model}`: {e}", "model": model_id, "tokens": 0}

    # 4. OpenRouter Universal Inference API (via OAuth Account or User API Key)
    from services.auth_service import get_auth_token as get_or_auth_token
    or_token = get_or_auth_token("openrouter") or keys.get("openrouter") or os.getenv("OPENROUTER_API_KEY") or ""

    if model_id.startswith("openrouter:") or (or_token and "openrouter" in model_id.lower()):
        actual_or_model = model_id.replace("openrouter:", "")
        api_msgs = []
        if system_prompt:
            api_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            api_msgs.append({"role": m["role"], "content": m["content"]})

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {or_token}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://127.0.0.1:8085",
                    "X-Title": "Agentic Desktop Control Center"
                },
                json={
                    "model": actual_or_model,
                    "messages": api_msgs,
                    "temperature": temperature
                },
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {}).get("total_tokens", len(content.split()))
                return {"role": "assistant", "content": content, "model": model_id, "tokens": usage}
            else:
                return {"role": "assistant", "content": f"**[OpenRouter Error ({resp.status_code})]** {resp.text}", "model": model_id, "tokens": 0}
        except Exception as e:
            return {"role": "assistant", "content": f"**[OpenRouter Connection Error]** {e}", "model": model_id, "tokens": 0}

    # 5. OpenAI / DeepSeek / Perplexity via OpenAI-compatible endpoints
    if "deepseek" in model_id.lower() and keys.get("deepseek"):
        endpoint = "https://api.deepseek.com/v1/chat/completions"
        api_key = keys.get("deepseek")
    elif "sonar" in model_id.lower() and keys.get("perplexity"):
        endpoint = "https://api.perplexity.ai/chat/completions"
        api_key = keys.get("perplexity")
    elif keys.get("openai"):
        endpoint = "https://api.openai.com/v1/chat/completions"
        api_key = keys.get("openai")
    else:
        endpoint = None
        api_key = None

    if endpoint and api_key:
        api_msgs = []
        if system_prompt:
            api_msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            api_msgs.append({"role": m["role"], "content": m["content"]})

        try:
            resp = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model_id, "messages": api_msgs, "temperature": temperature},
                timeout=45
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {}).get("total_tokens", len(content.split()))
                return {"role": "assistant", "content": content, "model": model_id, "tokens": usage}
        except Exception:
            pass

    # 4. If all live model execution channels failed, return the exact diagnostic error
    if "diag_msg" in locals() and diag_msg:
        error_report = (
            f"**[{model_id.upper()}] Model Execution Failed:**\n\n"
            f"{diag_msg}\n\n"
            f"👉 **To connect this model:**\n"
            f"• Authenticate your account or configure your API key in **⚙️ Settings**."
        )
    else:
        error_report = (
            f"**[{model_id.upper()}] Model Error:**\n\n"
            f"Could not connect to model provider for `{model_id}`.\n"
            f"Please ensure you are signed in or have entered a valid API key in **⚙️ Settings**."
        )

    return {
        "role": "assistant",
        "content": error_report,
        "model": model_id,
        "tokens": 0
    }
