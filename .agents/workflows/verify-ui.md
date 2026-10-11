# Workflow: /verify-ui

## Objective
Perform an end-to-end browser verification of the Meridian frontend application covering Use Cases 1 through 8.

## Requirements
- The application must be running locally via `make dev` or `make up`.
- The `browser_subagent` must be available.

## Steps
1. Invoke the browser subagent to navigate to `http://localhost:5173`.
2. Login as the selected Persona.
3. For each Use Case (UC1 to UC8):
   - Trigger the scenario in the chat.
   - Wait for streaming response and UI blocks to render.
   - Take a screenshot of the resulting UI block (e.g., transaction table, EMI breakdown).
   - If a confirmation card appears (e.g., card block, loan propose), interact with it and verify state updates.
4. Attach the generated screenshots to a final walkthrough report.
