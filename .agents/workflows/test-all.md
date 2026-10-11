# Workflow: /test-all

## Objective
Run the complete test suite and linters to verify the codebase against the Definition of Done.

## Steps
1. Run `make lint` (executes `ruff` checks).
2. Run `make typecheck` (executes `mypy --strict` and frontend TS checks).
3. Run `make test` (executes `pytest` with coverage requirements on backend and frontend tests).
4. Run `make eval` (runs routing evaluations against golden dataset).

## Success Criteria
All commands exit with code 0. Coverage must be >= 85%. Routing eval must be >= 90%.
Report the results clearly to the user, highlighting any failures.
