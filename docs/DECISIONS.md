# Architecture & Engineering Decisions

| Date | Context | Decision | Reason |
|---|---|---|---|
| 2026-10-10 | LLM Model Selection | Use `gemini-3.1-pro` for both the supervisor and specialist agents | `gemini-3.1-pro` provides superior reasoning required for complex LangGraph orchestration, function calling, and structured outputs while maintaining sufficient speed. We will validate its availability via the API on backend startup. |
| 2026-10-10 | Dependency Management | Use `uv` for the backend | As mandated by the plan, `uv` ensures fast, reliable, and consistent dependency resolution and installation. |
| 2026-10-10 | Frontend Scaffolding | Manual configuration over `create-vite` prompt | `create-vite` interactive prompts can cause issues with autonomous TTY terminals. We wrote the `package.json`, `vite.config.ts`, and `eslint.config.js` manually to ensure identical output without interactive hurdles. |
