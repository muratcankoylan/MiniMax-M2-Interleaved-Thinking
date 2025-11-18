# Contributing to MiniMax-M2 Interleaved Thinking Demo

Thank you for considering a contribution. This project demonstrates M miniMax-M2's interleaved reasoning in a minimal, reproducible way.

## How to Contribute

1. **Fork the repo** and create a branch off `main`.
2. **Add or update**:
   - Scenarios in `demo_runner.py` (see `SCENARIOS` dict)
   - Tools in `tools.py` (register in `TOOL_REGISTRY`)
   - Documentation in `README.md` or docstrings
3. **Run the demo** to ensure your changes produce valid traces:
   ```bash
   python demo_runner.py --scenario context_package
   ```
4. **Submit a PR** with:
   - Clear description of what changed
   - Screenshots of terminal output if UI-related
   - JSONL logs if you're adding new tool chains

## Style Guidelines

- Keep functions small and focused
- Use type hints where possible
- Document tool parameters in the OpenAI function schema
- Follow existing formatting (no trailing whitespace, 4-space indent)

## Testing

We don't have automated tests yet, but PRs should:
- Produce clean JSONL logs without errors
- Maintain backward compatibility with existing scenarios
- Document expected token counts and step counts in the PR description

## Questions?

Open an issue if you're unsure about a contribution direction. We're happy to discuss before you invest time in a PR.

