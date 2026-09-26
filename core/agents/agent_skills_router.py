"""
agent_skills_router.py - Senior Engineering Skills Router for Multi-Agent Pipeline
Dynamically matches and injects Addy Osmani's 24 engineering skills (https://github.com/addyosmani/agent-skills.git)
into prompt directives for Google Gemini, DeepSeek, ChatGPT, Claude, and all specialist workers.
"""

from typing import Dict, Any, List

# Agent Role -> Targeted Addy Osmani Engineering Skills Mapping
AGENT_SKILLS_MAP: Dict[str, List[Dict[str, str]]] = {
    "gemini": [
        {
            "skill": "Spec-Driven Development",
            "phase": "Define",
            "rule": "Define explicit goals, API contracts, invariants, constraints, and testable acceptance criteria before delegating."
        },
        {
            "skill": "Atomic Task Breakdown",
            "phase": "Plan",
            "rule": "Decompose monolithic prompts into atomic, self-contained worker milestones with no hidden dependencies."
        },
        {
            "skill": "Architectural Review",
            "phase": "Verify",
            "rule": "Audit all worker outputs against architectural modularity, data flow sanity, and specification compliance."
        }
    ],
    "deepseek": [
        {
            "skill": "Test-Driven Development (TDD)",
            "phase": "Build",
            "rule": "Structure code logic with verifiable assertions, input boundary testing, and concrete test cases."
        },
        {
            "skill": "Defensive Programming",
            "phase": "Build",
            "rule": "Include runtime null checks, graceful fallbacks, timeout safeguards, and robust error handling."
        },
        {
            "skill": "Code Simplifier",
            "phase": "Verify",
            "rule": "Eliminate dead abstractions, flatten nested conditional logic, and optimize for senior-grade readability."
        }
    ],
    "chatgpt": [
        {
            "skill": "Requirement Clarification & Copy Synthesis",
            "phase": "Define",
            "rule": "Format output with senior client-ready structure, clear typography, and formatted deliverable sections."
        },
        {
            "skill": "Release Verification",
            "phase": "Ship",
            "rule": "Perform pre-flight sanity checks on copy, links, variables, and cross-channel consistency."
        }
    ],
    "claude": [
        {
            "skill": "Architectural Review & Nuance Audit",
            "phase": "Verify",
            "rule": "Critique reasoning flow, modular boundaries, narrative depth, and edge-case omissions."
        },
        {
            "skill": "Security & Boundary Audit",
            "phase": "Verify",
            "rule": "Audit data leakage, unsanitized inputs, authorization boundaries, and defense-in-depth principles."
        },
        {
            "skill": "Accessibility (A11y) Review",
            "phase": "Verify",
            "rule": "Enforce semantic structure, keyboard accessibility, contrast ratios, and screen-reader readiness."
        }
    ],
    "perplexity": [
        {
            "skill": "Real-Time Source & Citation Verification",
            "phase": "Verify",
            "rule": "Verify factual claims against authoritative live web sources and provide direct, grounded citations."
        }
    ],
    "nvidia_ai": [
        {
            "skill": "Web Performance & Compute Optimization Audit",
            "phase": "Verify",
            "rule": "Profile computational scaling, Core Web Vitals (LCP, CLS, INP), asset footprints, and API throughput."
        }
    ],
    "dalle": [
        {
            "skill": "Visual Prompt Engineering & Layout Planning",
            "phase": "Build",
            "rule": "Provide precise aspect ratio calculations, composition guidelines, lighting parameters, and aesthetic style translation."
        }
    ],
    "meta_ai": [
        {
            "skill": "Viral Pattern & Engagement Optimization",
            "phase": "Build",
            "rule": "Optimize content hooks, platform retention patterns, and viral social formatting standards."
        }
    ],
    "copilot": [
        {
            "skill": "Enterprise Workflow & Office Automation",
            "phase": "Plan",
            "rule": "Coordinate office document schemas, data table formulas, and enterprise compliance guidelines."
        }
    ],
    "mistral": [
        {
            "skill": "Multilingual Logic & Utility Scripting",
            "phase": "Build",
            "rule": "Validate accurate multi-language syntax, fluent translation logic, and cost-efficient utility scripts."
        }
    ]
}

SUPERPOWERS_SKILLS_MAP: Dict[str, List[Dict[str, str]]] = {
    "gemini": [
        {
            "skill": "superpowers:brainstorming",
            "phase": "Spec",
            "rule": "Elicit clear specifications in digestible chunks before jumping into code synthesis."
        },
        {
            "skill": "superpowers:writing-plans",
            "phase": "Plan",
            "rule": "Produce implementation plans with atomic tasks, strict TDD red/green proofs, and DRY/YAGNI principles."
        },
        {
            "skill": "superpowers:dispatching-parallel-agents",
            "phase": "Orchestrate",
            "rule": "Dispatch independent subagents with fresh context and isolated acceptance boundaries."
        },
        {
            "skill": "superpowers:verification-before-completion",
            "phase": "Verify",
            "rule": "Run end-to-end verification and confirm all invariants pass before marking work complete."
        }
    ],
    "deepseek": [
        {
            "skill": "superpowers:test-driven-development",
            "phase": "Build",
            "rule": "Strict Red/Green TDD: Write failing assertions first, run them to prove failure, then write minimal code to pass."
        },
        {
            "skill": "superpowers:systematic-debugging",
            "phase": "Debug",
            "rule": "4-Phase Root-Cause investigation: Read stack trace, formulate single testable hypothesis, isolate minimal reproduction, fix cleanly without defensive guessing."
        },
        {
            "skill": "superpowers:subagent-driven-development",
            "phase": "Execute",
            "rule": "Execute assigned task in isolation, verify step-by-step, and request review upon completion."
        }
    ],
    "claude": [
        {
            "skill": "superpowers:requesting-code-review",
            "phase": "Review",
            "rule": "Review implementation diffs for code clarity, architectural integrity, edge-case coverage, and security boundaries."
        },
        {
            "skill": "superpowers:receiving-code-review",
            "phase": "Refine",
            "rule": "Address code review feedback systematically, verifying fixes with passing tests."
        }
    ]
}


def get_agent_skills_directive(agent_id: str, task_prompt: str = "") -> str:
    """
    Returns formatted Engineering Skills, Agency Personas, and dynamically imported skills
    from the skills/ directory matching the task prompt or agent role.
    """
    aid = agent_id.lower().strip()
    addy_skills = AGENT_SKILLS_MAP.get(aid, [])
    super_skills = SUPERPOWERS_SKILLS_MAP.get(aid, [])
    
    # Check if agent is an Agency Agent
    agency_agent_info = None
    try:
        from core.agency_agents_manager import agency_manager
        agency_agent_info = agency_manager.get_agent_by_id(aid)
    except Exception:
        pass

    # Check for matching dynamically ingested skills from skills/ folder
    dynamic_skills = []
    try:
        from core.skills_manager import skills_manager
        if task_prompt:
            dynamic_skills = skills_manager.match_skills_for_task(task_prompt, max_skills=2)
    except Exception:
        pass
    
    if not addy_skills and not super_skills and not agency_agent_info and not dynamic_skills:
        return ""
    
    directive = "\n=== APPLIED SENIOR ENGINEERING & SPECIALIST DIRECTIVES ===\n"
    if agency_agent_info:
        directive += f"Role: {agency_agent_info.get('name')} ({agency_agent_info.get('division_label')})\n"
        if agency_agent_info.get("vibe"):
            directive += f"Vibe & Tone: {agency_agent_info.get('vibe')}\n"
        if agency_agent_info.get("description"):
            directive += f"Mission: {agency_agent_info.get('description')}\n"
        directive += "\n"

    if dynamic_skills:
        directive += "--- Dynamically Active Skills (Claude AI Skills Vault) ---\n"
        for ds in dynamic_skills:
            directive += f"• Skill [{ds.get('name')}]: {ds.get('description')}\n"
            content = skills_manager.get_skill_content(ds.get("id"))
            if content:
                # Include concise key rules
                directive += f"  Instructions:\n{content[:500]}\n"
        directive += "\n"

    if addy_skills or super_skills:
        directive += "You are required to adhere to the following professional engineering standards:\n"
        for s in addy_skills:
            directive += f"- [{s['phase'].upper()}] {s['skill']}: {s['rule']}\n"
            
        if super_skills:
            directive += "\n--- Active Superpowers Protocols ---\n"
            for s in super_skills:
                directive += f"• [{s['phase'].upper()}] {s['skill']}: {s['rule']}\n"
                
    directive += "===========================================================\n\n"
    return directive



