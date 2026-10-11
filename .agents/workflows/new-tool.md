# Workflow: /new-tool

## Objective
Scaffold a new LLM tool, including its schema, implementation, registry entry, and unit tests.

## Context
Tools must adhere to the non-negotiable principles:
- No `customer_id` parameter exposed to the LLM (injected from context).
- Object-level authorization enforced.
- Write actions must be `propose_*` creating a `PendingAction`.

## Steps
1. Define the Pydantic schema for the tool inputs in the appropriate `_tools.py` file.
2. Implement the tool logic, utilizing dependency injection for core banking clients or services.
3. Add the tool to the `ToolRegistry` with the correct agent allowlist.
4. Write unit tests ensuring:
   - Happy path functionality.
   - Cross-customer data access denial.
   - Pydantic validation boundaries.
5. Provide a summary of the scaffolded tool to the user.
