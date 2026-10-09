# Architecture and Implementation Decisions

| Date | Context | Decision | Reason |
|---|---|---|---|
| 2026-10-09 | Gemini SDK usage | Use official `google-genai` SDK natively (no LangChain wrappers). | Avoid abstraction leaks and keep direct control over the Interaction API and streaming capabilities. |
| 2026-10-09 | Gemini Model Selection | Default to latest `gemini-2.5-flash` for agent loops, fallback to `gemini-2.5-pro` if needed. | Flash offers lowest latency for tool-calling loops, critical for real-time agent responsiveness. Model list will be validated dynamically on startup via the API. |
| 2026-10-09 | Mocking LLMs | Implement a custom `MockLLMClient` complying with the `LLMClient` protocol. | Allows tests, CI, and offline demos to pass predictably without API keys. |
| 2026-10-09 | Currency Representation | Use `Decimal` (Python) and `string` (JSON serialization) for all monetary values. | Prevent floating point precision errors. Adheres to Principle 2. |
| 2026-10-09 | Agent Action Execution | Only `propose_*` tools are available to agents. Execution is separated to `POST /actions/{id}/confirm`. | Enforces two-phase, human-confirmed writes (Principle 2). |
