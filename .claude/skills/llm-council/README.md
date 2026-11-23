# llm-council

A Claude skill that runs any question, idea, or decision through a council of 5
AI advisors who independently analyze it, peer-review each other anonymously,
and synthesize a final verdict. Adapted from Andrej Karpathy's LLM Council.

## Install

This skill lives at `.claude/skills/llm-council/SKILL.md`. Claude Code and Cowork
auto-discover skills in `.claude/skills/`, so no extra install step is needed
once this is in the repo.

## How to run it

Once installed, any of these trigger phrases summons a full council session on
whatever you're working on:

- `council this`            — the canonical trigger
- `run the council`         — when you've already framed the call
- `war room this`           — for higher-stakes decisions
- `pressure-test this`      — when you want it stress-attacked
- `stress-test this`        — same energy, different word
- `debate this`             — for genuinely contested questions

Type one of those followed by your question, with as much context as you can.
You get a visual HTML report (`council-report-[timestamp].html`) plus a full
markdown transcript (`council-transcript-[timestamp].md`).

### Example

```
council this: Should I build a $297 course on Claude Code for non-technical
solopreneurs, or is that the wrong move?
```

## Credit

Karpathy's LLM Council methodology · lead magnet by Alex Petkov
(Cost-Effective Software) · Claude skill by Ole Lehmann.
