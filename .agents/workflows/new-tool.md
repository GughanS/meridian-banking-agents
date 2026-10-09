# Workflow: /new-tool

**Description:** Scaffolds a new tool for an agent, including its Pydantic schema, implementation, registry entry, and unit tests.

**Steps:**
1. Ask the user for the tool's name, agent owner (Customer, Risk, or Credit), description, and expected parameters.
2. Create the Pydantic input schema in the relevant `tools/{agent}_tools.py` file.
3. Implement the tool logic, ensuring it delegates to deterministic services where appropriate.
4. Add the tool to the agent's allowlist in `tools/registry.py`.
5. Write unit tests for the tool in `tests/unit/tools/`.
6. Run `pytest` on the new tests to verify.
