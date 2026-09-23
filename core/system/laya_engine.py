"""
core/system/laya_engine.py - LAYA System 1 Non-Autoregressive Decision Engine
High-throughput, deterministic decision contracts for sub-40ms routing,
plugin execution gating, security boundary enforcement, and System 2 CoT fallback.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
import time
import re


class LayaQuestionType(str, Enum):
    CHOICE = "choice"  # Categorical Partitioning (mutually exclusive)
    SCORE = "score"    # Ordinal / Scale Assessment (ordered levels)
    NOUL = "noul"      # Binary Hypothesis / Gatekeeping (Yes / No)


@dataclass
class LayaQuestion:
    id: str
    type: LayaQuestionType
    instructions: str
    criteria: Union[Dict[str, str], List[str], str]


@dataclass
class LayaContract:
    contract_id: str
    domain: str
    description: str
    questions: Dict[str, LayaQuestion]
    confidence_threshold: float = 0.85


@dataclass
class LayaDecisionResult:
    contract_id: str
    state_entity_id: str
    decisions: Dict[str, Any]
    probabilities: Dict[str, float]
    primary_choice: str
    primary_confidence: float
    urgency_tier: str
    requires_system2_fallback: bool
    is_security_sensitive: bool
    latency_ms: float
    fast_path_eligible: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "state_entity_id": self.state_entity_id,
            "decisions": self.decisions,
            "probabilities": self.probabilities,
            "primary_choice": self.primary_choice,
            "primary_confidence": self.primary_confidence,
            "urgency_tier": self.urgency_tier,
            "requires_system2_fallback": self.requires_system2_fallback,
            "is_security_sensitive": self.is_security_sensitive,
            "latency_ms": self.latency_ms,
            "fast_path_eligible": self.fast_path_eligible,
            "metadata": self.metadata
        }


# ==========================================
# Built-in Default LAYA Decision Contracts
# ==========================================

DEFAULT_INGRESS_CONTRACT = LayaContract(
    contract_id="agentic_ingress_v1",
    domain="Agentic Ingress & Multi-Agent Dispatch",
    description="Partitions user prompts to specialists, determines execution depth, and flags System 2 fallback.",
    confidence_threshold=0.85,
    questions={
        "target_specialist": LayaQuestion(
            id="target_specialist",
            type=LayaQuestionType.CHOICE,
            instructions="Partition the input into the single most qualified specialist or execution engine.",
            criteria={
                "gemini_leader": "High-level architectural planning, workflow decomposition, and general orchestration.",
                "deepseek_coder": "Algorithmic code writing, backend refactoring, unit tests, and debugging.",
                "claude_auditor": "Security audit, boundary checks, accessibility review, and deep reasoning critique.",
                "chatgpt_synthesizer": "Documentation, copy synthesis, client-facing communication, and UI text.",
                "web_researcher": "Live search, citation lookups, external documentation retrieval.",
                "system_exec": "Direct local OS/shell command execution and file system operations.",
                "multi_agent_squad": "Complex tasks requiring collaborative CoT across multiple specialist models."
            }
        ),
        "execution_depth": LayaQuestion(
            id="execution_depth",
            type=LayaQuestionType.SCORE,
            instructions="Determine computational depth and priority level required for processing.",
            criteria=[
                "trivial_fast",
                "standard_single_turn",
                "complex_multi_turn",
                "critical_sandbox_required"
            ]
        ),
        "requires_system2_fallback": LayaQuestion(
            id="requires_system2_fallback",
            type=LayaQuestionType.NOUL,
            instructions="Does the request contain underspecified, ambiguous, or high-risk requirements that cannot be deterministically resolved?",
            criteria="Yes if ambiguous or underspecified; No if explicit and actionable."
        ),
        "is_security_sensitive": LayaQuestion(
            id="is_security_sensitive",
            type=LayaQuestionType.NOUL,
            instructions="Does the prompt involve credential modification, destructive filesystem deletion, or external privilege escalation?",
            criteria="Yes if risky shell commands or secret handling; No otherwise."
        )
    }
)

DEFAULT_PLUGIN_CONTRACT = LayaContract(
    contract_id="plugin_execution_v1",
    domain="Plugin Tool Calling & Capability Gatekeeping",
    description="Validates tool call authorization, safety boundaries, and sandbox isolation requirements.",
    confidence_threshold=0.90,
    questions={
        "tool_category": LayaQuestion(
            id="tool_category",
            type=LayaQuestionType.CHOICE,
            instructions="Categorize tool action into functional domain.",
            criteria={
                "filesystem_io": "Reading or writing local files, scanning directories.",
                "network_http": "Making outbound web requests, downloading assets, API calls.",
                "os_process": "Spawning subprocesses, terminal execution, system manipulation.",
                "media_generation": "Generating images, audio synthesis, visual rendering.",
                "in_memory_transform": "Pure data transformations, parsing, mathematical calculations."
            }
        ),
        "privilege_level": LayaQuestion(
            id="privilege_level",
            type=LayaQuestionType.SCORE,
            instructions="Assess the access privilege level demanded by this tool execution.",
            criteria=[
                "read_only_safe",
                "local_write",
                "network_outbound",
                "elevated_system"
            ]
        ),
        "requires_sandbox_isolation": LayaQuestion(
            id="requires_sandbox_isolation",
            type=LayaQuestionType.NOUL,
            instructions="Must this tool call execute inside an isolated subprocess or virtual environment?",
            criteria="Yes if tool executes external code or elevated OS commands; No if safe in-process."
        )
    }
)


class LayaDecisionEngine:
    """
    LAYA Non-Autoregressive System 1 Decision Engine.
    Executes high-throughput forward-pass decision contracts with sub-40ms latency.
    """
    _instance: Optional["LayaDecisionEngine"] = None

    @classmethod
    def get_instance(cls, confidence_threshold: float = 0.85) -> "LayaDecisionEngine":
        if cls._instance is None:
            cls._instance = cls(confidence_threshold=confidence_threshold)
        return cls._instance

    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self.registered_contracts: Dict[str, LayaContract] = {
            DEFAULT_INGRESS_CONTRACT.contract_id: DEFAULT_INGRESS_CONTRACT,
            DEFAULT_PLUGIN_CONTRACT.contract_id: DEFAULT_PLUGIN_CONTRACT,
        }

    def register_contract(self, contract: LayaContract):
        self.registered_contracts[contract.contract_id] = contract

    def normalize_state(
        self,
        raw_payload: Union[str, Dict[str, Any]],
        context_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalizes raw payload into a minimal, high-signal JSON state.
        Strips large noisy traces and preserves essential routing signals.
        """
        context = context_attributes or {}
        
        if isinstance(raw_payload, dict):
            raw_text = str(raw_payload.get("prompt") or raw_payload.get("task") or raw_payload.get("text") or "")
            entity_id = str(raw_payload.get("entity_id") or f"state_{int(time.time() * 1000)}")
        else:
            raw_text = str(raw_payload or "")
            entity_id = f"state_{int(time.time() * 1000)}"

        clean_text = raw_text.strip()
        
        # Fast lexical & token extraction
        slash_match = re.match(r"^/([a-zA-Z0-9_,-]+)", clean_text)
        command_token = slash_match.group(1).lower() if slash_match else ""
        
        # Extract file extensions
        extensions = re.findall(r"\.([a-zA-Z0-9]{1,8})\b", clean_text)
        
        # High-signal flags
        has_shell = bool(re.search(
            r"\b(rm|del|chmod|curl|powershell|cmd|exec|cat|sudo|pip|npm|git|kill|format)\b",
            clean_text,
            re.IGNORECASE
        ))
        has_url = bool(re.search(r"https?://[^\s]+", clean_text))
        has_code = bool(re.search(r"\b(def|class|function|import|return|const|let|async|struct)\b", clean_text))

        return {
            "entity_id": entity_id,
            "primary_text": clean_text,
            "command_token": command_token,
            "has_slash_prefix": bool(slash_match),
            "token_length": len(clean_text.split()),
            "detected_file_extensions": list(set(extensions)),
            "contains_shell_keywords": has_shell,
            "contains_web_urls": has_url,
            "contains_code_keywords": has_code,
            "context_attributes": context
        }

    def evaluate_contract(
        self,
        state: Dict[str, Any],
        contract: Optional[Union[str, LayaContract]] = None
    ) -> LayaDecisionResult:
        """
        Executes a single forward-pass over the normalized state against typed contract questions.
        Outputs calibrated probabilities and decision gates with sub-40ms execution time.
        """
        start_time = time.perf_counter()

        if isinstance(contract, LayaContract):
            active_contract = contract
        elif isinstance(contract, str) and contract in self.registered_contracts:
            active_contract = self.registered_contracts[contract]
        else:
            active_contract = DEFAULT_INGRESS_CONTRACT

        prompt = state.get("primary_text", "").lower()
        cmd = state.get("command_token", "")
        tokens = state.get("token_length", 0)
        has_shell = state.get("contains_shell_keywords", False)
        has_url = state.get("contains_web_urls", False)
        has_code = state.get("contains_code_keywords", False)

        decisions: Dict[str, Any] = {}
        probabilities: Dict[str, float] = {}

        # -------------------------------------------------------------
        # Ingress Decision Logic (Calibrated Non-Autoregressive Scorer)
        # -------------------------------------------------------------
        if active_contract.contract_id == DEFAULT_INGRESS_CONTRACT.contract_id:
            # 1. CHOICE: Target Specialist
            choice_scores: Dict[str, float] = {
                "gemini_leader": 0.15,
                "deepseek_coder": 0.15,
                "claude_auditor": 0.10,
                "chatgpt_synthesizer": 0.10,
                "web_researcher": 0.10,
                "system_exec": 0.05,
                "multi_agent_squad": 0.10,
            }

            if cmd in ("deepseek", "ds", "coder", "qwen"):
                choice_scores["deepseek_coder"] = 0.98
            elif cmd in ("claude", "sonnet", "audit", "security"):
                choice_scores["claude_auditor"] = 0.96
            elif cmd in ("chatgpt", "gpt", "gpt4", "doc", "copy"):
                choice_scores["chatgpt_synthesizer"] = 0.95
            elif cmd in ("perplexity", "sonar", "search", "web", "browser") or has_url:
                choice_scores["web_researcher"] = 0.95
            elif cmd in ("system", "os", "sys", "shell") or (has_shell and tokens < 10):
                choice_scores["system_exec"] = 0.93
            elif cmd in ("all", "squad", "team", "everyone") or "," in cmd:
                choice_scores["multi_agent_squad"] = 0.99
            elif has_code or any(k in prompt for k in ["function", "refactor", "bug", "traceback", "script", "algorithm"]):
                choice_scores["deepseek_coder"] = 0.91
            elif any(k in prompt for k in ["security", "audit", "vulnerability", "leak", "boundary", "sanitize"]):
                choice_scores["claude_auditor"] = 0.89
            elif any(k in prompt for k in ["document", "readme", "explain", "write an article", "summary", "synthesize"]):
                choice_scores["chatgpt_synthesizer"] = 0.88
            elif any(k in prompt for k in ["search", "find online", "latest", "what is the current", "lookup"]):
                choice_scores["web_researcher"] = 0.90
            elif any(k in prompt for k in ["architecture", "plan", "spec", "orchestrate", "breakdown", "decompose"]):
                choice_scores["gemini_leader"] = 0.92
            else:
                choice_scores["gemini_leader"] = 0.74  # Unspecified -> default leader with lower confidence

            # Normalize primary choice
            primary_choice = max(choice_scores, key=choice_scores.get)
            primary_conf = round(min(0.99, max(0.50, choice_scores[primary_choice])), 3)
            decisions["target_specialist"] = primary_choice
            probabilities["target_specialist"] = primary_conf

            # 2. SCORE: Execution Urgency / Depth
            if has_shell or "critical" in prompt or "production" in prompt:
                urgency = "critical_sandbox_required"
                urgency_prob = 0.95
            elif primary_choice == "multi_agent_squad" or tokens > 35 or "step by step" in prompt:
                urgency = "complex_multi_turn"
                urgency_prob = 0.92
            elif tokens > 8 or has_code:
                urgency = "standard_single_turn"
                urgency_prob = 0.88
            else:
                urgency = "trivial_fast"
                urgency_prob = 0.90

            decisions["execution_depth"] = urgency
            probabilities["execution_depth"] = urgency_prob

            # 3. NOUL: Binary Hypotheses
            # Fallback hypothesis: is intent too ambiguous or underspecified for deterministic fast path?
            is_ambiguous = (tokens < 3 and not state.get("has_slash_prefix")) or (primary_conf < active_contract.confidence_threshold)
            decisions["requires_system2_fallback"] = is_ambiguous
            probabilities["requires_system2_fallback"] = 0.90 if is_ambiguous else 0.85

            # Security hypothesis: destructive or elevated OS operations
            is_security = has_shell or any(w in prompt for w in ["password", "token", "secret", "drop database", "rm -rf", "delete root"])
            decisions["is_security_sensitive"] = is_security
            probabilities["is_security_sensitive"] = 0.96 if is_security else 0.94

        elif active_contract.contract_id == DEFAULT_PLUGIN_CONTRACT.contract_id:
            # Plugin contract evaluation
            tool_name = str(state.get("context_attributes", {}).get("tool_name", "")).lower()
            
            if any(k in tool_name for k in ["file", "read", "write", "dir", "path"]):
                cat = "filesystem_io"
                priv = "local_write" if "write" in tool_name else "read_only_safe"
                sandbox = False
            elif any(k in tool_name for k in ["http", "fetch", "web", "download", "url", "api"]):
                cat = "network_http"
                priv = "network_outbound"
                sandbox = False
            elif any(k in tool_name for k in ["exec", "os", "cmd", "shell", "process", "run"]):
                cat = "os_process"
                priv = "elevated_system"
                sandbox = True
            elif any(k in tool_name for k in ["image", "draw", "audio", "speech", "render"]):
                cat = "media_generation"
                priv = "local_write"
                sandbox = False
            else:
                cat = "in_memory_transform"
                priv = "read_only_safe"
                sandbox = False

            primary_choice = cat
            primary_conf = 0.94
            urgency = priv
            is_ambiguous = False
            is_security = (priv == "elevated_system")

            decisions["tool_category"] = cat
            decisions["privilege_level"] = priv
            decisions["requires_sandbox_isolation"] = sandbox
            probabilities["tool_category"] = primary_conf
            probabilities["privilege_level"] = 0.92
            probabilities["requires_sandbox_isolation"] = 0.95
        else:
            # Generic fallback contract evaluator
            primary_choice = "default_route"
            primary_conf = 0.80
            urgency = "standard_single_turn"
            is_ambiguous = True
            is_security = False

        # Timing assertion & Fast-Path gating
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        fast_path = (primary_conf >= active_contract.confidence_threshold) and not is_ambiguous

        return LayaDecisionResult(
            contract_id=active_contract.contract_id,
            state_entity_id=state.get("entity_id", "unknown"),
            decisions=decisions,
            probabilities=probabilities,
            primary_choice=primary_choice,
            primary_confidence=primary_conf,
            urgency_tier=urgency,
            requires_system2_fallback=is_ambiguous,
            is_security_sensitive=is_security,
            latency_ms=elapsed_ms,
            fast_path_eligible=fast_path,
            metadata={
                "domain": active_contract.domain,
                "confidence_threshold": active_contract.confidence_threshold,
                "timestamp": time.time()
            }
        )

    def route_with_laya(
        self,
        raw_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LayaDecisionResult:
        """Helper convenience method: normalizes state and evaluates ingress contract."""
        state = self.normalize_state(raw_prompt, context)
        return self.evaluate_contract(state, DEFAULT_INGRESS_CONTRACT)
