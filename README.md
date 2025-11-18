# Interleaved MiniMax Demo (Open Source Edition)

`interleaved_minimax` is a transparent, reproducible harness for showcasing MiniMax-M2’s interleaved thinking on real design-system artifacts. The project distills what we learned while building context-aware agents for front-end teams: keep the loop observable, keep the tooling grounded, and quantify efficiency against other LLMs.

---

## Why this exists

- **Explain interleaved thinking in practice.** Every reasoning burst, tool call, and result is streamed to the terminal and logged to disk, so practitioners can see *why* MiniMax-M2 course-corrects faster than linear agents.
- **Demonstrate agent-native workflows.** MiniMax calls bespoke tools (design tokens, component specs, pattern guidance) to build a design brief, exercising the same MCP/shell/browsers-style chains we see in production.
- **Benchmark against other coding LLMs.** The run summary emits live token counts and the equivalent MiniMax pricing (0.3 $/MTok in, 1.2 $/MTok out) so you can compare against GLM 4.6, K2 Thinking, Claude Sonnet 4.5, etc.
- **Serve as a starter kit for OSS contributions.** The code is intentionally small, well-documented, and easy to extend with additional tools or scenarios.

---

## Key learnings encoded here

1. **Interleaved > linear:** forcing the model to think after every tool result drastically reduces redundant calls in long-horizon front-end tasks.
2. **Grounded tools beat fabricated answers:** all tools read from `claude_minimax/examples/sample_project/`, ensuring explanations are backed by source material.
3. **Observability builds trust:** color-coded CLI output + JSONL logs make it trivial to review or share how MiniMax-M2 solved a task.
4. **Cost transparency matters:** developers need concrete $/token math when deciding between Claude, MiniMax, GLM, K2, etc., so we compute it every run.

---

## Architecture Overview

```
interleaved_minimax/
├── demo_runner.py   # CLI + orchestration + telemetry
├── tools.py         # Tool registry (design tokens, specs, patterns)
└── demo_logs/       # JSONL traces per run (auto-created)
```

### Components

- **`demo_runner.py`**
  - Loads API keys via repository-level `.env`
  - Defines scenarios (default: design-system brief, optional: front-end shipping plan)
  - Executes the MiniMax-M2 loop with `reasoning_split=True`
  - Streams colored output and writes logs with tool calls, reasoning, and usage stats

- **`tools.py`**
  - `get_design_tokens(category)` — pulls relevant sections from `design_system.md`
  - `get_component_spec(component)` — slices `component_specs.md`
  - `get_pattern_guidance(topic)` — queries `code_patterns.md`
  - Tool registry is centralized, making it easy to add new handlers (shell, retrieval, etc.)

---

## Interleaved workflow (context_package scenario)

1. System prompt instructs MiniMax-M2 to think after every tool result.
2. User prompt asks for a design brief with actionable sections (tokens, Button contract, composition pattern).
3. Model enters a loop:
   - emits a reasoning block (`Thought:`)
   - decides on a tool call (JSON args printed)
   - receives real data from the tool and updates the shared transcript
4. Loop continues until no more tool calls are needed; final response summarizes findings.
5. Post-run summary captures steps, calls, tokens, estimated MiniMax cost, and comparison reminders.

This matches MiniMax’s recommended API usage (`extra_body={"reasoning_split": True}` and preserving tool history), so you can copy the pattern into your own apps.

---

## Scenarios included

| Scenario | Purpose | Highlights |
| --- | --- | --- |
| `context_package` (default) | Design-system audit | Focuses on tokens, Button contract, composition patterns |
| `frontend_showcase` | Shipping a UI feature today | Emphasizes action items and how interleaved thinking shaved work |

Add more by editing the `SCENARIOS` dict in `demo_runner.py`.

### Tooling Surface

M2's interleaved thinking shines with tool use. The demo exposes three function tools that the model can call:

| Tool | Purpose | Data Source |
| --- | --- | --- |
| `get_design_tokens` | Fetch design-system tokens (colors, typography, spacing, shadows, border radius, breakpoints) | `design_system.md` |
| `get_component_spec` | Return specifications for UI components (Button, Card, Input, Modal, Alert) | `component_specs.md` |
| `get_pattern_guidance` | Look up development patterns and conventions (composition, naming, testing, etc.) | `code_patterns.md` |

M2's function calling works with both OpenAI-compatible and Anthropic-compatible APIs. After each tool result, M2 explicitly thinks about what it learned and adapts its strategy—unlike linear models that plan all tools upfront.

**Why this matters:**
- If a tool returns unexpected data (e.g., incomplete component spec), M2 adapts
- No wasted tokens on unnecessary tool calls
- Transparent reasoning: every decision is logged in `reasoning_details`
- Perfect for debugging and exploration workflows




---

## Getting Started

### Using MiniMax-M2 in Cursor

This demo was built using MiniMax-M2 integrated into [Cursor](https://cursor.com/), the AI-powered code editor. Here's how to set it up:

1. **Install Cursor**: Download from [cursor.com](https://cursor.com/)
2. **Configure API**: 
   - Open Cursor Settings → Models → API Keys
   - Enable "Override OpenAI Base URL"
   - Set base URL to `https://api.minimax.io/v1` (or `https://api.minimaxi.com/v1` for China)
   - Add your MiniMax API key from [platform.minimax.io](https://platform.minimax.io/user-center/basic-information/interface-key)
   - Select "MiniMax-M2" as the model
3. **Clear conflicts**: Remove any existing OpenAI environment variables (`OPENAI_API_KEY`, `OPENAI_BASE_URL`) to avoid conflicts

### Running the Demo

1. **Clone and install**:
```bash
git clone https://github.com/muratcankoylan/MiniMax-M2-Interleaved-Thinking
cd MiniMax-M2-Interleaved-Thinking
pip install -r requirements.txt
```

2. **Configure API**:
```bash
cp env.example .env
# Edit .env and add your MINIMAX_API_KEY
```

3. **Run**:
```bash
python demo_runner.py --scenario context_package
```

---

## Setup

1. Ensure `/Users/muratcankoylan/minimax/.env` (or your repo root) defines `MINIMAX_API_KEY` (MiniMax or compatible OpenAI key).
2. Install dependencies (same env used by `claude_minimax`):
   ```bash
   pip install -r claude_minimax/requirements.txt
   # minimally: pip install openai python-dotenv colorama
   ```

---

## Running the demo

```bash
cd /Users/muratcankoylan/minimax/interleaved_minimax
python demo_runner.py --scenario context_package      # design-system deep dive
# or
python demo_runner.py --scenario frontend_showcase    # front-end shipping plan
```

During the run you’ll see:

- Cyan banner summarizing MiniMax capabilities and pricing
- Step-by-step reasoning (“Thought”), tool calls, and tool results (color-coded)
- Final answer plus run summary (steps, tool calls, thinking bursts, token/cost math)
- A reminder to benchmark the cost profile against GLM 4.6, K2 Thinking, Claude Sonnet 4.5

Every event is also captured in `demo_logs/<timestamp>.jsonl` for replay or visualization.

---

## Tooling surface

| Tool | Backing data | Example usage |
| --- | --- | --- |
| `get_design_tokens` | `design_system.md` | `{"category": "colors"}` ⇒ primary palette + semantics |
| `get_component_spec` | `component_specs.md` | `{"component": "Button"}` ⇒ contract placeholder |
| `get_pattern_guidance` | `code_patterns.md` | `{"topic": "composition"}` ⇒ composition vs props |

Because these tools read real Markdown, editing the source docs immediately alters the model’s behavior—great for experiments or benchmarking different knowledge bases.

---

## Observability & Testing

- **CLI stream:** copy/paste-friendly output for threads, videos, or docs.
- **JSONL logs:** each object records `{step, thinking, tool_calls, tool_results, completion, usage}`—ideal for building dashboards or diffing different models.
- **Regression check:** `python demo_runner.py --scenario context_package` should finish in ~8 steps with ~7 tool calls. Compare token/cost results before/after modifications.

---

## Extending & Comparing

- **More tools:** plug shell commands, browser actions, or retrieval APIs into `TOOL_REGISTRY`.
- **Different models:** swap `MINIMAX_MODEL` in `.env` to run the exact workflow on GLM/K2/Claude and compare logs.
- **Visualization:** feed the JSONL trace into your favorite tooling (DAG viewer, metrics dashboards, etc.).
- **Contribution ideas:** add test harnesses, integrate MCP servers, build a Streamlit or browser UI, or script head-to-head benchmarks.

---

## Contributing

Contributions are welcome. Open an issue or PR if you want to add scenarios, tools, or visualizations. Please follow the existing code style and include tests where relevant.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

- Add new scenarios to `SCENARIOS` in `demo_runner.py`.
- Register additional tools in `tools.py` and expose them through `build_tools_spec`.
- Point the tool implementations at different documents if you want to showcase other workflows (API docs, test logs, etc.).

This minimal surface keeps the **interleaved loop** visible while still exercising multiple tool calls grounded in the project’s own artifacts. Use it for demos or regression tests when you update your toolset.


MiniMax-M2’s interleaved thinking thrives when we can show every decision, every tool call, and every dollar saved. This project keeps that loop visible—ready for open-source contributions, demos, and competitive benchmarks. Have fun building. 🙌
