"""
core/agent_workflows.py - Comprehensive OpenAI Agents & Autonomous Multi-Agent Workflow Engine
Implements OpenAI Agents workflows (https://github.com/openai/openai-agents-python) and Autonomous loop patterns.
"""

import time
from typing import List, Dict, Any, Generator, Optional
from services.llm_provider import generate_chat_response, load_api_keys


class AgentWorkflowType:
    SIMPLE_AGENT = "simple_agent"
    AGENT_FEEDBACK = "agent_feedback"
    AGENT_EXPERTS = "agent_experts"
    AGENT_EXPERTS_FEEDBACK = "agent_experts_feedback"
    PLANNER = "planner"
    RESEARCH_BOT = "research_bot"
    EVOLVE = "evolve"
    B2B = "b2b"
    SUPERVISOR_WORKER = "supervisor_worker"
    AUTONOMOUS = "autonomous"


PRESETS = {
    "coder": {
        "name": "Coder (Architect + Coder + Reviewer)",
        "type": AgentWorkflowType.AGENT_EXPERTS_FEEDBACK,
        "description": "Architect plans the technical structure, Coder implements, Reviewer performs QA and security checks.",
        "icon": "💻",
        "system_prompt": "You are a lead software engineering team solving complex programming problems.",
        "experts": [
            {"name": "System Architect", "role": "Deconstructs requirements and designs clean software architecture."},
            {"name": "Core Coder", "role": "Writes clean, robust, and idiomatic code implementation."},
            {"name": "QA & Security Reviewer", "role": "Inspects code for bugs, edge-cases, and optimization."}
        ],
        "max_iterations": 3
    },
    "experts_agent": {
        "name": "Experts Agent (Multi-Domain Ensemble)",
        "type": AgentWorkflowType.AGENT_EXPERTS,
        "description": "Main agent delegates queries to appropriate specialized subordinate expert agents.",
        "icon": "🧠",
        "system_prompt": "You are an AI Coordinator directing user questions to the most suitable domain expert.",
        "experts": [
            {"name": "Data Scientist", "role": "Mathematical analysis, algorithms, and data modeling."},
            {"name": "Systems Engineer", "role": "Infrastructure, DevOps, performance, and scaling."},
            {"name": "UX & Product Strategist", "role": "User experience, flow design, and ergonomics."}
        ],
        "max_iterations": 1
    },
    "planner": {
        "name": "Planner (Planner + Base Agent + Feedback)",
        "type": AgentWorkflowType.PLANNER,
        "description": "Planner breaks down task into subtasks -> Base agent executes -> Feedback evaluates and refines in a loop.",
        "icon": "📋",
        "system_prompt": "You are an agile project planner and execution team.",
        "experts": [],
        "max_iterations": 3
    },
    "research_bot": {
        "name": "Researcher (Planner + Searcher + Writer)",
        "type": AgentWorkflowType.RESEARCH_BOT,
        "description": "Planner prepares search phrases -> Searcher finds information & summarizes -> Writer creates deep structured report.",
        "icon": "🔬",
        "system_prompt": "You are a rigorous deep research laboratory team producing executive research intelligence.",
        "experts": [],
        "max_iterations": 1
    },
    "simple_agent": {
        "name": "Simple Agent (Direct Solver)",
        "type": AgentWorkflowType.SIMPLE_AGENT,
        "description": "A single focused agent completes the task with zero overhead.",
        "icon": "⚡",
        "system_prompt": "You are a direct, concise, and highly effective AI solver.",
        "experts": [],
        "max_iterations": 1
    },
    "writer_feedback": {
        "name": "Writer with Feedback (Draftsman + Editor)",
        "type": AgentWorkflowType.AGENT_FEEDBACK,
        "description": "Writer generates draft -> Editor critiques style, clarity, and depth in an iterative refinement loop.",
        "icon": "✍️",
        "system_prompt": "You are a professional editorial team producing high-impact publications.",
        "experts": [],
        "max_iterations": 3
    },
    "b2b": {
        "name": "2 Bots (B2B Collaborative Dialogue)",
        "type": AgentWorkflowType.B2B,
        "description": "Two AI bots interact in continuous collaborative dialogue while keeping the human in the loop.",
        "icon": "🤖",
        "system_prompt": "Two specialized AI agents engage in constructive debate and synthesis.",
        "experts": [
            {"name": "Alpha Agent (Visionary)", "role": "Generates ideas, proposals, and explores creative options."},
            {"name": "Beta Agent (Pragmatist)", "role": "Challenges assumptions, optimizes details, and refines feasibility."}
        ],
        "max_iterations": 4
    },
    "supervisor_worker": {
        "name": "Supervisor + Worker (Manager Delegation Loop)",
        "type": AgentWorkflowType.SUPERVISOR_WORKER,
        "description": "Supervisor translates user goal into structured worker instructions and monitors completion.",
        "icon": "👔",
        "system_prompt": "Supervisor oversees specialized worker task completion.",
        "experts": [],
        "max_iterations": 3
    },
    "evolve": {
        "name": "Evolve (Genetic Multi-Candidate Optimizer)",
        "type": AgentWorkflowType.EVOLVE,
        "description": "Generates parallel parent solutions -> Chooser selects superior response -> Feedback improves -> Next generation.",
        "icon": "🧬",
        "system_prompt": "Evolutionary optimization framework producing superior refined outputs.",
        "experts": [],
        "max_iterations": 2
    },
    "autonomous": {
        "name": "Agent (Autonomous Auto-GPT Loop)",
        "type": AgentWorkflowType.AUTONOMOUS,
        "description": "Self-directed reasoning loop with critique, subtask decomposition, and auto-stop/always-continue options.",
        "icon": "♾️",
        "system_prompt": "You are an autonomous agent capable of self-dialogue, critique, and continuous execution.",
        "experts": [],
        "max_iterations": 4
    }
}


def run_agent_workflow(
    task: str,
    workflow_type: str = AgentWorkflowType.AGENT_EXPERTS_FEEDBACK,
    model_id: str = "gemini-2.0-flash",
    preset_key: Optional[str] = None,
    max_iterations: int = 3,
    auto_stop: bool = True,
    custom_experts: Optional[List[Dict[str, str]]] = None,
    system_prompt: str = ""
) -> Generator[Dict[str, Any], None, None]:
    """
    Executes a Multi-Agent workflow pattern and yields step-by-step telemetry events.
    Yields event dicts: {"step": int, "agent": str, "role": str, "content": str, "status": str, "is_final": bool}
    """
    step_count = 0
    preset = PRESETS.get(preset_key, {}) if preset_key else {}
    base_sys_prompt = system_prompt or preset.get("system_prompt", "You are a helpful AI team.")

    # ─────────────────────────────────────────────────────────────
    # 1. SIMPLE AGENT
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.SIMPLE_AGENT:
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Primary Agent",
            "role": "Executor",
            "content": f"Processing task: \"{task}\"",
            "status": "thinking",
            "is_final": False
        }
        res = generate_chat_response([{"role": "user", "content": task}], model_id=model_id, system_prompt=base_sys_prompt)
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Primary Agent",
            "role": "Executor",
            "content": res.get("content", ""),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 2. AGENT WITH FEEDBACK LOOP
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.AGENT_FEEDBACK:
        current_draft = ""
        for i in range(1, max_iterations + 1):
            step_count += 1
            yield {
                "step": step_count,
                "agent": "Creator Agent",
                "role": "Drafting",
                "content": f"Generation iteration {i}/{max_iterations}...",
                "status": "thinking",
                "is_final": False
            }

            prompt = task if i == 1 else f"Original Task: {task}\n\nPrevious Draft:\n{current_draft}\n\nFeedback for improvement:\n{feedback_text}\n\nPlease generate a revised, higher-quality response addressing all feedback."
            res = generate_chat_response([{"role": "user", "content": prompt}], model_id=model_id, system_prompt=base_sys_prompt)
            current_draft = res.get("content", "")

            step_count += 1
            yield {
                "step": step_count,
                "agent": "Creator Agent",
                "role": "Draft Produced",
                "content": current_draft,
                "status": "running",
                "is_final": False
            }

            # Feedback evaluation step
            step_count += 1
            yield {
                "step": step_count,
                "agent": "Feedback Evaluator",
                "role": "Critic",
                "content": "Evaluating draft quality and verifying requirements...",
                "status": "thinking",
                "is_final": False
            }

            eval_prompt = f"Evaluate this response for the task: \"{task}\"\n\nDraft:\n{current_draft}\n\nIs this response fully satisfactory, correct, and complete? Answer with PASS or provide specific improvement points."
            eval_res = generate_chat_response([{"role": "user", "content": eval_prompt}], model_id=model_id, system_prompt="You are a strict, objective quality reviewer. If good, start with PASS.")
            feedback_text = eval_res.get("content", "")

            step_count += 1
            is_pass = "PASS" in feedback_text.upper()[:20] or i == max_iterations
            yield {
                "step": step_count,
                "agent": "Feedback Evaluator",
                "role": "Critic",
                "content": feedback_text,
                "status": "evaluated",
                "is_final": is_pass
            }

            if is_pass and auto_stop:
                break

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Final Output",
            "role": "Synthesized",
            "content": current_draft,
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 3. AGENT WITH EXPERTS
    # ─────────────────────────────────────────────────────────────
    if workflow_type in (AgentWorkflowType.AGENT_EXPERTS, AgentWorkflowType.AGENT_EXPERTS_FEEDBACK):
        experts = custom_experts or preset.get("experts", [
            {"name": "Technical Specialist", "role": "Architectural and implementation details."},
            {"name": "Domain Analyst", "role": "Contextual logic and data verification."}
        ])

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Chief Orchestrator",
            "role": "Router",
            "content": f"Analyzing task to route to {len(experts)} attached experts: {', '.join([e['name'] for e in experts])}",
            "status": "thinking",
            "is_final": False
        }

        expert_contributions = []
        for exp in experts:
            step_count += 1
            yield {
                "step": step_count,
                "agent": exp["name"],
                "role": exp["role"],
                "content": f"Analyzing task through {exp['name']} perspective...",
                "status": "running",
                "is_final": False
            }

            exp_prompt = f"Role: {exp['name']} ({exp['role']})\n\nTask: {task}\n\nProvide your specialized analysis, solution components, and technical recommendations."
            res = generate_chat_response([{"role": "user", "content": exp_prompt}], model_id=model_id, system_prompt=base_sys_prompt)
            out = res.get("content", "")
            expert_contributions.append(f"### Expert Contribution: {exp['name']}\n{out}")

            step_count += 1
            yield {
                "step": step_count,
                "agent": exp["name"],
                "role": exp["role"],
                "content": out,
                "status": "running",
                "is_final": False
            }

        # Synthesis
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Chief Orchestrator",
            "role": "Synthesizer",
            "content": "Synthesizing all expert recommendations into a unified, complete solution...",
            "status": "thinking",
            "is_final": False
        }

        synth_prompt = f"Task: {task}\n\nExpert Reports:\n" + "\n\n".join(expert_contributions) + "\n\nPlease synthesize a unified, comprehensive, and polished final response."
        synth_res = generate_chat_response([{"role": "user", "content": synth_prompt}], model_id=model_id, system_prompt=base_sys_prompt)
        final_text = synth_res.get("content", "")

        # Optional feedback loop
        if workflow_type == AgentWorkflowType.AGENT_EXPERTS_FEEDBACK:
            step_count += 1
            yield {
                "step": step_count,
                "agent": "Lead QA Reviewer",
                "role": "Feedback Loop",
                "content": "Verifying synthesized solution against all expert criteria...",
                "status": "thinking",
                "is_final": False
            }

            qa_prompt = f"Task: {task}\n\nSynthesized Output:\n{final_text}\n\nPerform final quality validation and output the final refined deliverable."
            qa_res = generate_chat_response([{"role": "user", "content": qa_prompt}], model_id=model_id, system_prompt="You are a principal QA validator polishing the final product.")
            final_text = qa_res.get("content", final_text)

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Final Deliverable",
            "role": "Output",
            "content": final_text,
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 4. PLANNER WORKFLOW (Planner + Base + Feedback)
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.PLANNER:
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Planner Agent",
            "role": "Decomposition",
            "content": f"Deconstructing task \"{task}\" into sequential execution plan...",
            "status": "thinking",
            "is_final": False
        }

        plan_prompt = f"Deconstruct the following task into a structured, step-by-step execution roadmap:\nTask: {task}"
        plan_res = generate_chat_response([{"role": "user", "content": plan_prompt}], model_id=model_id, system_prompt="You are a master strategist who builds actionable plans.")
        plan_text = plan_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Planner Agent",
            "role": "Plan Ready",
            "content": plan_text,
            "status": "running",
            "is_final": False
        }

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Execution Agent",
            "role": "Implementation",
            "content": "Executing all tasks according to the roadmap...",
            "status": "thinking",
            "is_final": False
        }

        exec_prompt = f"Original Task: {task}\n\nExecution Plan:\n{plan_text}\n\nExecute all steps and produce the complete, finished deliverable."
        exec_res = generate_chat_response([{"role": "user", "content": exec_prompt}], model_id=model_id, system_prompt=base_sys_prompt)
        exec_text = exec_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Feedback Agent",
            "role": "Verification",
            "content": "Validating execution against original requirements...",
            "status": "thinking",
            "is_final": False
        }

        fb_prompt = f"Requirement: {task}\n\nDelivered Solution:\n{exec_text}\n\nPerform final polish and output the finalized deliverable."
        fb_res = generate_chat_response([{"role": "user", "content": fb_prompt}], model_id=model_id, system_prompt="You are a strict QA auditor finalizing deliverables.")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Final Output",
            "role": "Delivered",
            "content": fb_res.get("content", exec_text),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 5. RESEARCH BOT (Planner + Searcher + Writer)
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.RESEARCH_BOT:
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Research Planner",
            "role": "Search Formulation",
            "content": f"Formulating research queries for: \"{task}\"",
            "status": "thinking",
            "is_final": False
        }

        q_prompt = f"Generate 5 targeted, high-value search queries and key investigation angles for:\nTopic: {task}"
        q_res = generate_chat_response([{"role": "user", "content": q_prompt}], model_id=model_id, system_prompt="You are an intelligence researcher formulating deep queries.")
        queries_text = q_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Information Gatherer",
            "role": "Discovery & Extraction",
            "content": f"Simulating intelligence collection for queries:\n{queries_text}",
            "status": "thinking",
            "is_final": False
        }

        gather_prompt = f"Topic: {task}\n\nInvestigation Queries:\n{queries_text}\n\nGather key facts, structural knowledge, empirical findings, and data points."
        gather_res = generate_chat_response([{"role": "user", "content": gather_prompt}], model_id=model_id, system_prompt="You extract and summarize high-density knowledge.")
        findings_text = gather_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Technical Writer",
            "role": "Synthesis & Publication",
            "content": "Compiling final executive intelligence report...",
            "status": "thinking",
            "is_final": False
        }

        write_prompt = f"Topic: {task}\n\nResearch Findings:\n{findings_text}\n\nWrite a polished, highly detailed, and structured research report with clear sections, conclusions, and takeaways."
        write_res = generate_chat_response([{"role": "user", "content": write_prompt}], model_id=model_id, system_prompt=base_sys_prompt)

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Research Report",
            "role": "Deliverable",
            "content": write_res.get("content", ""),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 6. B2B (Bot-to-Bot Dialogue)
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.B2B:
        bot1_name = "Bot Alpha (Advocate)"
        bot2_name = "Bot Beta (Inquisitor)"
        history = []
        last_turn = f"Human provided discussion topic: {task}"

        for turn in range(1, max_iterations + 1):
            active_bot = bot1_name if turn % 2 != 0 else bot2_name
            other_bot = bot2_name if turn % 2 != 0 else bot1_name

            step_count += 1
            yield {
                "step": step_count,
                "agent": active_bot,
                "role": f"Dialogue Turn {turn}/{max_iterations}",
                "content": f"Analyzing statement from {other_bot} and formulating response...",
                "status": "thinking",
                "is_final": False
            }

            b_prompt = f"Topic: {task}\n\nConversation so far:\n" + "\n\n".join(history[-4:]) + f"\n\nRespond directly to {other_bot}'s points, advance the reasoning, and suggest specific solutions."
            b_res = generate_chat_response([{"role": "user", "content": b_prompt}], model_id=model_id, system_prompt=f"You are {active_bot} participating in a collaborative discussion.")
            reply = b_res.get("content", "")
            history.append(f"**{active_bot}**: {reply}")

            step_count += 1
            yield {
                "step": step_count,
                "agent": active_bot,
                "role": "Response",
                "content": reply,
                "status": "running",
                "is_final": False
            }

        # Final synthesis
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Dialogue Synthesizer",
            "role": "Synthesis",
            "content": "Synthesizing consensus and key conclusions from the Bot-to-Bot discussion...",
            "status": "thinking",
            "is_final": False
        }

        s_prompt = f"Discussion Topic: {task}\n\nFull Transcript:\n" + "\n\n".join(history) + "\n\nProduce the final consolidated consensus, actionable conclusions, and key insights."
        s_res = generate_chat_response([{"role": "user", "content": s_prompt}], model_id=model_id, system_prompt=base_sys_prompt)

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Consensus Deliverable",
            "role": "Final",
            "content": s_res.get("content", ""),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 7. SUPERVISOR + WORKER
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.SUPERVISOR_WORKER:
        step_count += 1
        yield {
            "step": step_count,
            "agent": "Supervisor",
            "role": "Task Delegation",
            "content": f"Decomposing user request: \"{task}\" into worker directive...",
            "status": "thinking",
            "is_final": False
        }

        sup_prompt = f"User Request: {task}\n\nFormulate precise technical instructions and deliverables for your specialized worker."
        sup_res = generate_chat_response([{"role": "user", "content": sup_prompt}], model_id=model_id, system_prompt="You are a senior supervisor providing crystal clear instructions.")
        directive = sup_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Specialist Worker",
            "role": "Execution",
            "content": f"Executing supervisor directive:\n{directive[:180]}...",
            "status": "thinking",
            "is_final": False
        }

        worker_prompt = f"Goal: {task}\n\nSupervisor Instructions:\n{directive}\n\nExecute the work completely and provide the completed deliverable."
        worker_res = generate_chat_response([{"role": "user", "content": worker_prompt}], model_id=model_id, system_prompt=base_sys_prompt)
        worker_output = worker_res.get("content", "")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Supervisor",
            "role": "Review & Approval",
            "content": "Reviewing worker results for completion...",
            "status": "thinking",
            "is_final": False
        }

        review_prompt = f"User Query: {task}\n\nWorker Deliverable:\n{worker_output}\n\nVerify and package the final polished response for the user."
        review_res = generate_chat_response([{"role": "user", "content": review_prompt}], model_id=model_id, system_prompt="You are the supervisor delivering the finished result.")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Final Output",
            "role": "Delivered",
            "content": review_res.get("content", worker_output),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 8. EVOLVE (Genetic Candidate Optimization)
    # ─────────────────────────────────────────────────────────────
    if workflow_type == AgentWorkflowType.EVOLVE:
        candidates = []
        for c_idx in range(1, 3):
            step_count += 1
            yield {
                "step": step_count,
                "agent": f"Parent Agent #{c_idx}",
                "role": "Candidate Generator",
                "content": f"Generating candidate solution #{c_idx}...",
                "status": "thinking",
                "is_final": False
            }
            c_res = generate_chat_response([{"role": "user", "content": f"Task: {task}\n\nApproach variant #{c_idx}."}], model_id=model_id, system_prompt=base_sys_prompt)
            candidates.append(c_res.get("content", ""))

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Evolutionary Chooser",
            "role": "Fitness Evaluation",
            "content": "Evaluating candidate solutions against optimal fitness metrics...",
            "status": "thinking",
            "is_final": False
        }

        choose_prompt = f"Goal: {task}\n\nCandidate 1:\n{candidates[0]}\n\nCandidate 2:\n{candidates[1]}\n\nSelect the best elements from both candidates, eliminate flaws, and synthesize the ultimate evolved response."
        evolved_res = generate_chat_response([{"role": "user", "content": choose_prompt}], model_id=model_id, system_prompt="You are a genetic optimizer fusing the best traits into a superior solution.")

        step_count += 1
        yield {
            "step": step_count,
            "agent": "Evolved Solution",
            "role": "Optimal Output",
            "content": evolved_res.get("content", ""),
            "status": "completed",
            "is_final": True
        }
        return

    # ─────────────────────────────────────────────────────────────
    # 9. AUTONOMOUS (Auto-GPT Self-Dialogue Loop)
    # ─────────────────────────────────────────────────────────────
    state_context = f"Goal: {task}"
    for step in range(1, max_iterations + 1):
        step_count += 1
        yield {
            "step": step_count,
            "agent": f"Autonomous Agent (Step {step})",
            "role": "Self-Reasoning & Action",
            "content": f"Executing autonomous cycle {step}/{max_iterations}...",
            "status": "thinking",
            "is_final": False
        }

        auto_prompt = f"{state_context}\n\nPerform Step {step}: Assess current state, apply critical reflection, identify next concrete actions, execute them, and evaluate if goal is achieved."
        auto_res = generate_chat_response([{"role": "user", "content": auto_prompt}], model_id=model_id, system_prompt="You are an autonomous agent using self-dialogue, critique, and step-by-step reasoning.")
        thought = auto_res.get("content", "")
        state_context += f"\n\nStep {step} Output:\n{thought}"

        step_count += 1
        is_done = step == max_iterations
        yield {
            "step": step_count,
            "agent": f"Autonomous Agent (Step {step})",
            "role": "Action Executed",
            "content": thought,
            "status": "running",
            "is_final": is_done
        }

    step_count += 1
    yield {
        "step": step_count,
        "agent": "Autonomous Outcome",
        "role": "Goal Accomplished",
        "content": state_context,
        "status": "completed",
        "is_final": True
    }
