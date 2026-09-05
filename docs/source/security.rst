Security & Safeguards
=====================

Security policies and isolation guarantees:

* **Credential Masking**: Server passwords, SSH private keys, and authorization secrets are strictly sanitized from LLM prompt contexts.
* **OS Command Safeguards**: Execution via `cmd.sys_exec` is restricted to authorized agent turns with `auto_cwd` resolution.
* **Local Data Sovereignty**: Conversation database (`db.sqlite`) and auth sessions remain strictly on your local disk.
