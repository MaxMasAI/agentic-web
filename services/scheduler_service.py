"""
services/scheduler_service.py - Crontab / Task Scheduler Background Engine
"""

import os
import json
import time
import subprocess
import sys

SCHEDULER_FILE = os.path.join("json", "scheduler_jobs.json")


def load_scheduler_jobs() -> list:
    if os.path.exists(SCHEDULER_FILE):
        try:
            with open(SCHEDULER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_scheduler_jobs(jobs: list):
    os.makedirs("json", exist_ok=True)
    with open(SCHEDULER_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)


def add_scheduler_job(name: str, task_prompt: str, interval_minutes: int, agents: str = "auto") -> dict:
    jobs = load_scheduler_jobs()
    job = {
        "id": f"job_{int(time.time())}",
        "name": name,
        "task": task_prompt,
        "agents": agents,
        "interval_minutes": max(1, interval_minutes),
        "last_run": "Never",
        "next_run": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + interval_minutes * 60)),
        "status": "ACTIVE",
        "run_count": 0
    }
    jobs.append(job)
    save_scheduler_jobs(jobs)
    return job


def delete_scheduler_job(job_id: str):
    jobs = [j for j in load_scheduler_jobs() if j.get("id") != job_id]
    save_scheduler_jobs(jobs)
