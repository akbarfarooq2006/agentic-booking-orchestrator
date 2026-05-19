---
trigger: always_on
---

Rule: If the user requests an AI agent, multi-agent system, tool-calling agent, workflow agent, or anything described as “using OpenAI Agents SDK”, always implement it with the official OpenAI Agents SDK — not with direct Chat Completions API usage.

Required:
- Use the official OpenAI Agents SDK package and APIs
- Use SDK-native constructs (Agent, Runner, Tools, Handoffs, Memory, Sessions, etc.)
- Follow official SDK patterns and architecture

Forbidden unless explicitly requested:
- Building the agent manually with chat.completions.create()
- Simulating agents with custom loops
- Replacing SDK workflows with raw API orchestration