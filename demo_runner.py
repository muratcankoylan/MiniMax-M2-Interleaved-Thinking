"""Interleaved thinking demo for MiniMax M2."""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_REGISTRY


SCENARIOS = {
    "context_package": {
        "user_prompt": (
            "You are the MiniMax-M2 coding assistant embedded in a front-end system design review. "
            "Produce a crisp brief for the design system team that highlights: (1) critical design "
            "tokens, (2) the Button implementation contract, and (3) one reusable development pattern "
            "to protect. Use the provided tools after every thought instead of guessing. The audience "
            "cares about interleaved reasoning efficiency, so weave in how each artifact supports fast "
            "front-end iteration."
        )
    },
    "frontend_showcase": {
        "user_prompt": (
            "MiniMax-M2 is pair-programming on a front-end build. Analyze the available documents, "
            "select the most relevant tokens, component specs, and patterns, and draft an action plan "
            "for shipping a polished UI section today. Explicitly call out how interleaved thinking cut "
            "down redundant work and why this model is ideal for UI-heavy workflows."
        )
    },
}

SYSTEM_PROMPT = (
    "You are MiniMax-M2 running in interleaved mode. Think after every tool result, adjust your "
    "plan, and keep reasoning transparent. If you call multiple tools, clearly integrate their "
    "outputs before responding."
)

COST_PER_INPUT_TOKEN = 0.3 / 1_000_000  # $0.3 / MTokens
COST_PER_OUTPUT_TOKEN = 1.2 / 1_000_000  # $1.2 / MTokens


def color(text: str, tone: str) -> str:
    return f"{tone}{text}{Style.RESET_ALL}"


def print_banner(run_id: str, scenario: str) -> None:
    headline = color("MiniMax-M2 Interleaved Thinking Demo", Fore.CYAN + Style.BRIGHT)
    sub = (
        "Agent-native • 10B activated params • 8% of Claude Sonnet price • "
        "2x faster loops • Front-end & game dev specialist"
    )
    pricing = (
        f"Pricing: input ${0.3}/MTok | output ${1.2}/MTok | starter plan $10/mo "
        f"(10% of Claude Code Max)."
    )
    brief = (
        "Brief focus: interleaved thinking, tool orchestration, Mini price / max performance."
    )
    print("=" * 90)
    print(f"{headline}\n{color(sub, Fore.WHITE)}")
    print(color(pricing, Fore.LIGHTGREEN_EX))
    print(color(brief, Fore.LIGHTBLUE_EX))
    print(color(f"Scenario: {scenario} | Run ID: {run_id}", Fore.MAGENTA))
    print("=" * 90 + "\n")


def print_step_header(step: int) -> None:
    print(color(f"\n── Step {step} ────────────────────────────────────────────────", Fore.LIGHTBLUE_EX))


def summarize_tool_result(tool: str, payload: str, max_chars: int = 220) -> str:
    preview = payload[:max_chars].rstrip()
    if len(payload) > max_chars:
        preview += " ..."
    return f"{tool}: {preview}"


def calc_cost(prompt_tokens: int, completion_tokens: int) -> Tuple[float, float, float]:
    input_cost = prompt_tokens * COST_PER_INPUT_TOKEN
    output_cost = completion_tokens * COST_PER_OUTPUT_TOKEN
    return input_cost, output_cost, input_cost + output_cost


def build_tools_spec() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_design_tokens",
                "description": "Fetch design-system tokens such as colors, typography, spacing, or shadows.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Token category to retrieve",
                            "enum": ["colors", "typography", "spacing", "shadows", "border radius", "breakpoints"],
                        }
                    },
                    "required": ["category"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_component_spec",
                "description": "Return the spec for a UI component such as Button, Card, Input, Modal, or Alert.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "description": "Component name; e.g. Button",
                        }
                    },
                    "required": ["component"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pattern_guidance",
                "description": "Look up development patterns and conventions (composition, naming, testing, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Pattern topic to retrieve",
                        }
                    },
                    "required": ["topic"],
                },
            },
        },
    ]


def load_client() -> OpenAI:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    load_dotenv()  # allow local overrides if present
    api_key = os.getenv("MINIMAX_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2")

    if not api_key:
        raise RuntimeError("Missing MINIMAX_API_KEY. Copy env.example and set your key.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    client._default_model = model  # type: ignore[attr-defined]
    return client


def run_demo(scenario: str) -> None:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Options: {list(SCENARIOS)}")

    colorama_init(autoreset=True)
    client = load_client()
    tools_spec = build_tools_spec()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SCENARIOS[scenario]["user_prompt"]},
    ]

    log_dir = Path(__file__).parent / "demo_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{run_id}.jsonl"

    def log_event(event: Dict[str, Any]) -> None:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event))
            handle.write("\n")

    step = 0
    tool_invocations = 0
    thinking_segments = 0
    print_banner(run_id, scenario)

    while True:
        step += 1
        print_step_header(step)
        response = client.chat.completions.create(  # type: ignore[attr-defined]
            model=getattr(client, "_default_model", "MiniMax-M2"),
            messages=messages,
            tools=tools_spec,
            extra_body={"reasoning_split": True},
        )
        choice = response.choices[0]
        message = choice.message
        thinking = ""
        if hasattr(message, "reasoning_details") and message.reasoning_details:
            thinking = message.reasoning_details[0].get("text", "")

        tool_call_payloads = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    tool_call_payloads.append(tc.model_dump())
                except AttributeError:
                    tool_call_payloads.append(
                        {
                            "id": getattr(tc, "id", None),
                            "type": getattr(tc, "type", None),
                            "function": getattr(tc, "function", None),
                        }
                    )

        log_event(
            {
                "step": step,
                "type": "assistant",
                "thinking": thinking,
                "content": message.content,
                "tool_calls": tool_call_payloads,
            }
        )

        assistant_record: Dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
        }
        if tool_call_payloads:
            assistant_record["tool_calls"] = tool_call_payloads
        messages.append(assistant_record)

        if thinking:
            thinking_segments += 1
            wrapped = textwrap.fill(thinking, width=88)
            print(color("Thought:", Fore.LIGHTYELLOW_EX))
            print(color(wrapped, Fore.WHITE))

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments or "{}")
                tool_invocations += 1
                print(color(f"Tool Call ▶ {tool_name} {json.dumps(tool_args)}", Fore.LIGHTGREEN_EX))

                handler = TOOL_REGISTRY.get(tool_name)
                if not handler:
                    raise RuntimeError(f"No handler registered for tool {tool_name}")

                result = handler(**tool_args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
                log_event({"step": step, "type": "tool_result", "tool": tool_name, "result": result})
                print(color("Tool Result ⬅", Fore.GREEN))
                print(color(textwrap.fill(summarize_tool_result(tool_name, result), width=88), Fore.WHITE))

            continue

        if message.content:
            print(color("\nFinal Response", Fore.CYAN + Style.BRIGHT))
            print(color(textwrap.fill(message.content, width=88), Fore.WHITE))
        usage_payload: Dict[str, Any] = {}
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            try:
                usage_payload = usage.model_dump()
            except AttributeError:
                usage_payload = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                }

        log_event(
            {
                "step": step,
                "type": "completion",
                "content": message.content,
                "usage": usage_payload,
            }
        )
        prompt_tokens = int(usage_payload.get("prompt_tokens") or 0)
        completion_tokens = int(usage_payload.get("completion_tokens") or 0)
        input_cost, output_cost, total_cost = calc_cost(prompt_tokens, completion_tokens)

        print(color("\nRun Summary", Fore.CYAN + Style.BRIGHT))
        summary_lines = [
            f"Steps: {step}",
            f"Tool calls: {tool_invocations}",
            f"Thinking segments: {thinking_segments}",
            f"Prompt tokens: {prompt_tokens:,} (${input_cost:.6f})",
            f"Completion tokens: {completion_tokens:,} (${output_cost:.6f})",
            f"Estimated total: ${total_cost:.6f} (≈8% Claude Sonnet 4.5)",
            "Differentiators: interleaved reasoning, rapid tool chaining, 10B activated params.",
            "Use this cost/latency profile to benchmark against GLM 4.6, K2 Thinking, and Claude Sonnet 4.5.",
        ]
        for line in summary_lines:
            print(color(f"• {line}", Fore.LIGHTWHITE_EX))
        break

    print(color(f"\nLog saved to {log_path}", Fore.LIGHTBLUE_EX))


def main() -> None:
    parser = argparse.ArgumentParser(description="MiniMax M2 interleaved thinking demo")
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS.keys(),
        default="context_package",
        help="Scenario to run",
    )
    args = parser.parse_args()
    run_demo(args.scenario)


if __name__ == "__main__":
    main()


