import asyncio
import os
import sys

# Ensure root directory in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser.browser_helpers import wait_until_text_settles

# Map input/output DOM selectors for all browser-automated agents.
# Input selectors are listed in priority order (tried one-by-one).
AGENT_SELECTORS = {
    "gemini": {
        "input": [
            "rich-textarea div[contenteditable='true']",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".model-response-text, message-content, .response-container-content"
    },
    "deepseek": {
        "input": [
            "textarea#chat-input",
            "textarea",
            "div[contenteditable='true']"
        ],
        "response": "div.ds-markdown, .chat-response, .markdown-content"
    },
    "chatgpt": {
        "input": [
            "div#prompt-textarea[contenteditable='true']",
            "div[contenteditable='true'][data-lexical-editor='true']",
            "div[contenteditable='true']"
        ],
        "response": "div[data-message-author-role='assistant']"
    },
    # DALL-E 3 opens via chatgpt.com — use same selectors as ChatGPT
    "dalle": {
        "input": [
            "div#prompt-textarea[contenteditable='true']",
            "div[contenteditable='true'][data-lexical-editor='true']",
            "div[contenteditable='true']"
        ],
        "response": "div[data-message-author-role='assistant']"
    },
    "claude": {
        "input": [
            "div[contenteditable='true'].ProseMirror",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".font-claude-message, .message-content, article"
    },
    "meta_ai": {
        "input": [
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".markdown, .assistant-message, div[role='presentation']"
    },
    "perplexity": {
        "input": [
            "div#ask-input",                          # Primary: confirmed working (2026)
            "div[role='textbox']",                    # Fallback: role-based
            "textarea[placeholder]",                  # Legacy fallback
            "textarea"
        ],
        "response": ".prose, .markdown, [data-testid='answer-text']"
    },
    "copilot": {
        "input": [
            "textarea[name='q']",
            "div[role='textbox']",
            "textarea#searchbox",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".attribution-type, [data-testid='copilot-response'], .acReply, .message-response"
    },
    "nvidia_ai": {
        "input": [
            "textarea[placeholder]",
            "div[role='textbox']",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".markdown, .response-content, .chat-message"
    },
    "mistral": {
        "input": [
            "textarea[placeholder]",
            "div[role='textbox']",
            "div[contenteditable='true']",
            "textarea"
        ],
        "response": ".markdown, .message-content, [class*='message']"
    }
}

async def talk_to_agent(agent_id, page, prompt_text):
    """Submits a prompt to a specific agent page, waits for output to settle, and records chat ID."""
    print(f"\n[{agent_id.upper()}] Submitting prompt...")
    await page.bring_to_front()

    # Prepend unified thread header if not already formatted
    if "Collaborative AI review framework assignment" not in prompt_text:
        formatted_prompt = f"[THREAD: Collaborative AI review framework assignment]\n{prompt_text}"
    else:
        formatted_prompt = prompt_text
    
    selectors = AGENT_SELECTORS.get(agent_id, {
        "input": ["textarea", "div[contenteditable='true']"],
        "response": ".markdown, p"
    })
    
    input_selectors = selectors["input"]
    if isinstance(input_selectors, str):
        input_selectors = [input_selectors]

    # Try each input selector in order until one is visible
    input_box = None
    for sel in input_selectors:
        try:
            await page.wait_for_selector(sel, timeout=12000, state="visible")
            candidate = page.locator(sel).first
            if await candidate.is_visible():
                input_box = candidate
                break
        except Exception:
            continue

    if input_box is None:
        raise RuntimeError(
            f"[{agent_id.upper()}] Could not find a visible input box. "
            f"Tried: {input_selectors}"
        )

    await input_box.click()
    await input_box.fill(formatted_prompt)
    await input_box.press("Enter")
    
    await asyncio.sleep(3)
    response_locator = page.locator(selectors["response"]).last
    output = await wait_until_text_settles(response_locator)
    print(f"[{agent_id.upper()}] Output received ({len(output)} chars)")

    # Automatically capture and persist the exact chat session URL/ID
    try:
        from utils.chat_session_manager import save_agent_chat_url
        current_url = page.url
        save_agent_chat_url(agent_id, current_url)
    except Exception:
        pass

    return output
