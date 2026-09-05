Context & Long-Term Memory
==========================

Conversation history and persistent memory storage system.

Architecture
------------
* **SQLite Database (`db.sqlite`)**: High-performance relational storage for contexts and messages.
* **Mirrored Text Logs (`logs/chats/*.txt`)**: Human-readable disk mirrors formatted with timestamps.
* **Auto-Titling**: Context summaries generated automatically like ChatGPT.
* **Context Toggle**: Easily enable or disable multi-turn history injection in Settings.
