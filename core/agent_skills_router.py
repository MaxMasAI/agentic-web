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

def get_agent_skills_directive(agent_id: str) -> str:
    """
    Returns formatted Addy Osmani Engineering Skills prompt block for the designated agent.
    """
    skills = AGENT_SKILLS_MAP.get(agent_id.lower(), [])
    if not skills:
        return ""
    
    directive = "\n=== APPLIED SENIOR ENGINEERING SKILLS (Addy Osmani Agent-Skills) ===\n"
    directive += "You are required to adhere to the following professional engineering standards:\n"
    for s in skills:
        directive += f"- [{s['phase'].upper()}] {s['skill']}: {s['rule']}\n"
    directive += "====================================================================\n\n"
    return directive
