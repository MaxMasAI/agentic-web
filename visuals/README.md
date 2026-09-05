# 🖼️ Visual Verification Directory (`visuals/`)

This directory contains automated browser screenshots captured during each phase of multi-agent task execution for visual auditing and quality verification.

---

## 📸 Captured Milestones

| Filename | Capture Stage | Purpose |
|---|---|---|
| `step_gemini_plan.png` | **Leader Planning** | Captures Google Gemini's decomposed plan and subtask breakdown in the Chrome window. |
| `step_[agent_id].png` | **Worker Execution** | Captures each worker's active prompt execution (e.g. `step_deepseek.png`, `step_chatgpt.png`). |
| `step_gemini_review.png` | **Leader Audit** | Captures the leadership review and final approval milestone. |
| `step_final_output.png` | **Final Assembly** | Full-page screenshot of the finalized deliverable. |

---

## 🔍 Visual Inspection

- All screenshots in this folder are previewable in real-time under the **Folder Explorer (`🖼️ visuals/`)** tab on the Streamlit dashboard (`http://localhost:8501`).
