# Workflow: /verify-ui

**Description:** Triggers the browser agent to perform an end-to-end verification of the UI for Use Cases 1-8.

**Steps:**
1. Ensure the application is running (`make up`).
2. Invoke the browser subagent to open `http://localhost:5173`.
3. Sequentially execute Use Cases 1 through 8.
4. Capture screenshots at the completion of each use case or crucial intermediate steps (e.g., confirmation cards).
5. Compile the results into a markdown report with attached screenshots.
