# Insight-Linker

Insight-Linker is a lightweight Python CLI tool for insider risk triage. It combines user activity logs, HR context, and access privileges to identify potentially suspicious events and generate an explainable Markdown report.

This project was built as a small MVP to explore how infrastructure-style operational data can be connected with governance and security context in an auditable, readable, and extensible way.

---

## Why this project matters

Insider risk is rarely visible from a single log source alone. A file access event may look normal in isolation, but become more meaningful when combined with HR status, such as leave or resignation notice, and access privilege context.

Insight-Linker is a practice project designed to model that idea in code by correlating multiple context sources, assigning a simple risk score, explaining why an event was flagged, and generating a readable report for review.

---

## Features

- Load sample JSON data for user activity events, HR context, and access privileges.
- Evaluate each event with a rule-based scoring engine.
- Classify events as **Low / Medium / High** based on the current MVP scoring logic.
- Return structured results through an `EvaluationResult` dataclass.
- Attach human-readable reasons to each risk decision.
- Generate a Markdown report focused on Medium and High risk events.

---

## Example use case

A user accesses a sensitive file path:

- during leave
- after hours after a resignation notice
- outside their allowed resource scope

The tool scores the event and records the reasons behind the result so the outcome is not just a label, but an explainable finding.

---

## Project structure

```text
.
├─ app/
│  ├─ core_engine.py      # Risk scoring logic
│  ├─ loader.py           # JSON -> dataclass loaders
│  ├─ models.py           # Domain models and EvaluationResult
│  └─ report_gen.py       # Markdown report generator
│
├─ data/
│  └─ raw/
│     ├─ access_privileges.json
│     ├─ hr_context.json
│     └─ user_activity.json
│
├─ outputs/
│  └─ (generated) insight reports
│
├─ main.py
└─ README.md
```

### Modules

- `loader.py`  
  Loads sample JSON data into typed Python objects.

- `models.py`  
  Defines the domain model:
  - `UserActivity`
  - `HRContext`
  - `AccessPrivilege`
  - `EvaluationResult`

- `core_engine.py`  
  Applies scoring logic and returns a structured evaluation result.

- `report_gen.py`  
  Builds a Markdown report for human review.

- `main.py`  
  Entry point that loads data, evaluates activities, prints results, and generates the report.

---

## Current scoring logic

The current MVP includes three explicit example rules:

- Access during leave
- After-hours access by a resignation-notified user
- Access to an unauthorized resource path

These rules are intentionally small and explicit so the project remains easy to understand and extend.

---

## Tech stack

- Python 3.13.13
- Python `dataclasses`
- JSON sample inputs
- Rule-based scoring logic
- Markdown report generation

No external dependencies are required for the current MVP.

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/tomohitotoyomura-hub/insight-linker.git
cd insight-linker
```

### 2. Create and activate a virtual environment (optional)

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Run the project

```bash
python main.py
```

---

## What the script does

When you run `python main.py`, the tool will:

1. Load sample activity, HR, and privilege data from `data/raw/`
2. Evaluate each activity with the scoring engine
3. Print the evaluation results to the console
4. Generate a Markdown report under `outputs/` with a timestamped filename

---

## Sample console output

```text
Insight-Linker MVP setup complete
Loaded user activities: 5
Loaded HR contexts: 3
Loaded access privileges: 3

=== Evaluation Results ===
user_id=u001, timestamp=2026-05-02T21:49:00, risk_level=Low, risk_score=0, reasons=[]
user_id=u002, timestamp=2026-05-01T02:15:00, risk_level=Medium, risk_score=2, reasons=['Access during leave']
user_id=u003, timestamp=2026-05-01T10:05:00, risk_level=Low, risk_score=0, reasons=[]
user_id=u001, timestamp=2026-05-01T23:45:00, risk_level=Medium, risk_score=3, reasons=['After-hours access by resignation-notified user']
user_id=u002, timestamp=2026-05-01T01:30:00, risk_level=High, risk_score=5, reasons=['Access during leave', 'Access to unauthorized resource']

Markdown report generated: outputs/20260504_073214_insight_report.md
```

This sample reflects the verified Day6 state after `EvaluationResult` integration, while preserving the same observable scoring behavior as earlier MVP output.

---

## Sample report output

A generated report includes summary statistics and detailed findings for Medium and High risk events.

Example:

```markdown
# Insight-Linker Risk Report

Generated at: 2026-05-04T07:32:14
Target period: 2026-05-01 (sample data)
Unique users: 3
Scoring profile: MVP v1 (3 rules: leave status, resignation notice, unauthorized access)

## Summary

- Total events: 5
- High risk events: 1 (20%)
- Medium risk events: 2 (40%)
- Low risk events: 2 (40%)

## High Risk Findings

### User u002 / 2026-05-01T01:30:00
- Risk level: High
- Risk score: 5
- Reasons: Access during leave, Access to unauthorized resource
```

The current report also includes a Medium Risk Findings section and a Notes section in the generated output.

---

## Design goals

This project was built with the following goals in mind:

- **Explainability**  
  Every flagged event should include reasons, not just a score.

- **Traceability**  
  Output should be easy to inspect and reuse in reports.

- **Simplicity**  
  The MVP uses explicit rules and small modules instead of opaque logic.

- **Extensibility**  
  The structure should make it easy to add more rules, more input sources, improved reporting, and stronger error handling for missing context.

---

## Development progress

This repository was developed incrementally as a small hands-on project.

Current completed milestones include:

- Day 1: Local environment setup
- Day 2: Domain models and sample JSON creation
- Day 3: Loader implementation
- Day 4: First scoring engine and Low / Medium / High validation
- Day 5: Markdown report generation
- Day 6: `EvaluationResult` integration and output structure cleanup

---

## Possible next steps

Planned or possible future improvements include:

- Group findings by user
- Handle missing HR or privilege context more explicitly
- Enrich report formatting
- Add tests
- Add input validation
- Support additional insider risk scenarios

---

## Why I built this

I have a background in IT infrastructure operations and am building toward roles in insider risk, security operations, IT risk, and GRC.

Insight-Linker is a small portfolio project that reflects that transition by combining:

- operational log thinking
- security triage logic
- governance-oriented reporting
- explainable output design

---

## Notes

- All data in this repository is sample data for MVP development.
- This is a learning and portfolio project, not a production-ready detection platform.
- Detailed work logs and code explanation notes are currently managed locally and are not included in this repository.

---

## License

MIT