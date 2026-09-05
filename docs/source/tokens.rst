Tokens & Context Management
===========================

Understanding token utilization and context limits is critical for optimal AI inference and cost management.

Overview
--------
Tokens are the basic building blocks used by LLMs to process text and code. Each provider and model has specific context window constraints and pricing per token.

Token Estimation & Counting
---------------------------
- **Tiktoken Integration**: Uses OpenAI's fast byte-pair encoding engine for exact token counts.
- **Provider Adapters**: Automatic tokenizer selection for Anthropic Claude, Google Gemini, Ollama, and OpenRouter models.
- **Dynamic Context Slicing**: Automatically trims older conversational history when approaching context limits while preserving system instructions and key memory summaries.

Configuring Limits
------------------
Context limits and max output tokens can be adjusted in the application settings under:
**Settings > Model Configuration > Max Output Tokens & Context Window**.
