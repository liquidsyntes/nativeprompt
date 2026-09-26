## 2026-09-26T21:22:17Z

<USER_REQUEST>
You are the SWE Light orchestrator (teamwork_preview_swe).
Your working directory is: c:\nativeprompt\.agents\teamwork\swe_1
The project root is: c:\nativeprompt
The authoritative user request is stored at: c:\nativeprompt\.agents\teamwork\ORIGINAL_REQUEST.md

Task summary:
Create a simple, minimalist, and functional Gradio-based web interface for nativeprompt.
The command `nativeprompt web` should launch the local web server.
This is a focused, self-contained task.

Requirements:
- R1: Integrate `web` command into the nativeprompt CLI to launch the local Gradio server.
- R2: Gradio UI allowing user to enter an initial prompt, select/input target model (e.g. gpt-5.6, claude-opus-5), and see the improved prompt along with applied rules/explanations. Directly use internal API of `nativeprompt`.

Acceptance Criteria:
- Automated test (e.g. tests/test_web.py) verifying Gradio interface logic and prompt processing.
- `python -m nativeprompt web --help` works and does not fail.
- All pytest tests pass cleanly without breaking existing tests.

Please run your SWE Light workflow (implementer, reviewer rounds, test execution). Maintain progress.md and BRIEFING.md in your working directory. When complete and fully verified, report completion to parent with your final handoff summary.
</USER_REQUEST>
