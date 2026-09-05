"""
discussion.py - Multi-Agent Discussion & Debate Protocol
Each worker agent reviews all other workers' outputs and submits
a critique or improvement suggestion. Gemini then moderates
and synthesizes the best ideas before the final approval stage.
"""

import asyncio

async def run_discussion_round(
    task,
    workers,
    worker_outputs,
    tabs,
    talk_fn,
    gemini_tab,
    rounds=1
):
    """
    Conducts a structured multi-round discussion between all worker agents.

    Args:
        task          : Original user task string.
        workers       : List of worker agent dicts (from agentlist).
        worker_outputs: Dict of {agent_id: output_text} from initial execution.
        tabs          : Dict of {agent_id: Playwright page}.
        talk_fn       : Reference to talk_to_agent(agent_id, page, prompt).
        gemini_tab    : Playwright page for the Gemini Leader.
        rounds        : Number of discussion rounds (default 1).

    Returns:
        refined_outputs : Updated dict of {agent_id: refined_output}.
        discussion_log  : Full string log of the discussion for dashboard.
    """
    refined_outputs = dict(worker_outputs)
    discussion_log = ""

    for round_num in range(1, rounds + 1):
        print(f"\n{'='*50}")
        print(f"  DISCUSSION ROUND {round_num} — AGENTS CRITIQUING EACH OTHER")
        print(f"{'='*50}")
        discussion_log += f"\n\n=== DISCUSSION ROUND {round_num} ===\n"

        critiques = {}

        # Step A: Each worker reviews all other workers' outputs
        for reviewer in workers:
            r_id = reviewer["id"]
            r_tab = tabs.get(r_id)
            if not r_tab:
                continue

            # Compile all other agents' outputs for review
            others_context = ""
            for other in workers:
                if other["id"] != r_id:
                    o_out = refined_outputs.get(other["id"], "")
                    others_context += (
                        f"--- {other['name'].upper()} OUTPUT ---\n{o_out}\n\n"
                    )

            my_output = refined_outputs.get(r_id, "")

            critique_prompt = (
                f"You are {reviewer['name']} ({reviewer['role']}) participating "
                f"in a quality discussion about this task:\n\n"
                f"TASK: '{task}'\n\n"
                f"YOUR OWN INITIAL OUTPUT:\n{my_output}\n\n"
                f"OTHER AGENTS' OUTPUTS:\n{others_context}"
                "You must now:\n"
                "1. Identify the BEST idea or element from the other agents' outputs.\n"
                "2. Identify any WEAKNESS or GAP in your own output.\n"
                "3. Write an IMPROVED version of your output that incorporates "
                "the best elements from all agents.\n\n"
                "Format your response:\n"
                "BEST ELEMENT FROM OTHERS: [describe]\n"
                "GAP IN MY OUTPUT: [describe]\n"
                "IMPROVED OUTPUT:\n[your revised, enhanced output here]\n\n"
                "IMPORTANT: Respond ONLY in English."
            )

            print(f"\n  [{reviewer['name']}] Writing critique and revision...")
            critique = await talk_fn(r_id, r_tab, critique_prompt)
            critiques[r_id] = critique
            discussion_log += (
                f"\n[{reviewer['name']}] CRITIQUE:\n{critique}\n"
            )

            # Extract refined output from the IMPROVED OUTPUT section
            if "IMPROVED OUTPUT:" in critique:
                improved = critique.split("IMPROVED OUTPUT:")[1].strip()
                refined_outputs[r_id] = improved
            else:
                refined_outputs[r_id] = critique

        # Step B: Gemini moderates and synthesizes the best of the round
        print(f"\n  [Gemini Leader] Moderating discussion round {round_num}...")
        all_critiques = ""
        for w in workers:
            c = critiques.get(w["id"], "No critique.")
            all_critiques += f"--- {w['name'].upper()} CRITIQUE ---\n{c}\n\n"

        moderation_prompt = (
            "You are the Leader (Gemini) moderating a discussion between "
            f"your specialist agents about this task:\n\nTASK: '{task}'\n\n"
            f"Agent Critiques and Revised Outputs (Round {round_num}):\n"
            f"{all_critiques}\n"
            "Your role as moderator is to:\n"
            "1. Identify the STRONGEST ideas from across all agents.\n"
            "2. Identify any remaining gaps or conflicts.\n"
            "3. Issue a MODERATION DIRECTIVE telling each agent "
            "what specific aspect to focus on or improve in the next round "
            "(or in the final output if this is the last round).\n\n"
            "Format:\n"
            "STRONGEST IDEAS: [list]\n"
            "REMAINING GAPS: [list]\n"
            "MODERATION DIRECTIVE: [specific instructions per agent]\n\n"
            "IMPORTANT: Respond ONLY in English."
        )

        moderation = await talk_fn("gemini", gemini_tab, moderation_prompt)
        discussion_log += (
            f"\n[GEMINI MODERATION - ROUND {round_num}]:\n{moderation}\n"
        )
        print(f"  [Gemini Leader] Moderation complete for round {round_num}.")

    return refined_outputs, discussion_log
