Files & Attachments
===================

Manage document uploads, images, datasets, and file-based context retrieval.

Upload Policies
---------------
* **Workdir Upload Directory**: Stores local copies of uploaded files inside the workspace.
* **Native Upload API**: When supported by OpenAI / Anthropic / Gemini, files are uploaded directly via native endpoints.
* **Multimodal Images**: Upload PNG/JPG/WebP images as multimodal vision context.
* **RAG Document Processing**: PDF, DOCX, TXT, and Markdown files are embedded into local vector indexes.

Collision Prevention
--------------------
When saving files without overwrite flags, automatic timestamp versioning prefixes files (`YYYY-MM-DD_HH-MM-SS_<filename>`).
