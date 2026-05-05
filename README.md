# Insight-Linker

Insight-Linker is a lightweight Python CLI tool for insider risk triage. It combines user activity logs, HR context, and access privileges to identify potentially suspicious events and generate an explainable Markdown report.

This project was built as a small MVP to explore how infrastructure-style operational data can be connected with governance and security context in an auditable, readable, and extensible way.

---

## Why I built this

I built this project to connect raw technical activity data with HR, legal, and governance context, because insider risk is rarely visible from logs alone.

This repository also reflects a personal transition from infrastructure operations toward insider risk, security operations, IT risk, and GRC-oriented work.

Insight-Linker is therefore not just a coding exercise. It is a small portfolio project designed to show how operational log thinking, explainable triage logic, and governance-oriented reporting can be combined in one MVP.

---

## Why this project matters

A single file access event may look normal in isolation, but become more meaningful when combined with HR status such as leave or resignation notice, and access privilege context.

Insight-Linker models that idea in code by correlating multiple context sources, assigning a simple risk score, explaining why an event was flagged, and generating a readable report for review.

The Day7 and Day8 extensions push that idea further by adding session-level and user-level views, so suspicious behavior can be reviewed not only as an isolated event but also as a behavioral pattern over time.

---

## Features

- Load sample JSON data for user activity events, HR context, and access privileges.
- Evaluate each event with a rule-based scoring engine.
- Classify events as **Low / Medium / High** based on the current MVP scoring logic.
- Return structured results through an `EvaluationResult` dataclass.
- Attach human-readable reasons to each risk decision.
- Generate a Markdown report focused on Medium and High risk events.
- Group Day7 sample logs into sessions and calculate session-level risk.
- Aggregate final user-level risk based on session outcomes.
- Include session-level and user-level risk tables in the generated Markdown report.

---

## Example use case

A file access event may become more meaningful when it occurs during leave, after hours following a resignation notice, or outside the user’s allowed resource scope.

The tool scores the event and records the reasons behind the result so the outcome is not just a label, but an explainable finding.

The Day7 extension also groups activity over time, allowing suspicious behavior to be assessed as a session pattern rather than only as a single event.

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
│  ├─ access_privileges.json
│  ├─ hr_context.json
│  ├─ user_activity.json
│  └─ day7_sample_logs.csv
│
├─ outputs/
│  └─ (generated) insight reports
│
├─ requirements.txt
├─ day7_analysis.py       # Session and user-level risk aggregation
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
  Applies event-level scoring logic and returns a structured evaluation result.

- `report_gen.py`  
  Builds a Markdown report for human review, including event-level findings and Day7 session/user summaries when available.

- `day7_analysis.py`  
  Groups log events into 30-minute sessions, scores each session, and aggregates final user-level risk.

- `main.py`  
  Entry point that loads data, evaluates activities, prints results, runs Day7 analysis, and generates the report.

---

## Current scoring logic

The current MVP includes three explicit example rules:

- Access during leave.
- After-hours access by a resignation-notified user.
- Access to an unauthorized resource path.

These rules are intentionally small and explicit so the project remains easy to understand, validate, and extend.

---

## Day7 session analysis

In addition to event-level scoring, the project includes a Day7 analysis step that groups log events into user sessions and derives a higher-level risk view.

The goal is to move beyond isolated events and highlight risky behavior patterns across a session or across a user’s recent activity.

### Session grouping

Events are grouped by `user_id` and ordered by timestamp.

A new session starts when the gap between two consecutive events is **30 minutes or more**.

Each session includes:

- `user_id`
- `session_id`
- `session_start`
- `session_end`
- `duration_seconds`
- `event_count`

### Session scoring rules

Each session is scored using a small rule-based model.

Current Day7 rules include:

- Night-time activity (`22:00-05:59 JST`)
- Access to `/restricted/` resources
- Download of restricted resources
- Permission change activity
- One or more denied actions
- Multiple denied actions within the same session

Sessions are then classified as:

- **High** for score `>= 6`
- **Medium** for score `>= 3`
- **Low** otherwise

### User-level aggregation

After session scoring, the tool also builds a user-level summary.

For each user, the final risk level is based on the highest session risk observed across that user’s sessions.

The aggregation also includes:

- total session score
- total session count
- number of High sessions
- number of Medium sessions
- number of Low sessions

---

## Tech stack

- Python 3.13.13
- Python `dataclasses`
- JSON sample inputs
- CSV sample input for Day7 session analysis
- Rule-based scoring logic
- Markdown report generation
- `pandas` for Day7 session aggregation

The core MVP logic is implemented in Python modules, while Day7 adds tabular session analysis on top of the event-level model.

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the project

```bash
python main.py
```

---

## What the script does

When you run `python main.py`, the tool will:

1. Load sample activity, HR, and privilege data from `data/`.
2. Evaluate each activity with the scoring engine.
3. Print the event-level evaluation results to the console.
4. Run Day7 session analysis on sample log data.
5. Print session-level and user-level risk tables.
6. Generate a Markdown report under `outputs/` with a timestamped filename.

---

## Sample console output

```text
Insight-Linker MVP setup complete
Loaded user activities: 5
Loaded HR contexts: 3
Loaded access privileges: 3

=== Evaluation Results (per activity) ===
user_id=u001, timestamp=2026-05-02T21:49:00, risk_level=Low, risk_score=0, reasons=[]
user_id=u002, timestamp=2026-05-01T02:15:00, risk_level=Medium, risk_score=2, reasons=['Access during leave']
user_id=u003, timestamp=2026-05-01T10:05:00, risk_level=Low, risk_score=0, reasons=[]
user_id=u001, timestamp=2026-05-01T23:45:00, risk_level=Medium, risk_score=3, reasons=['After-hours access by resignation-notified user']
user_id=u002, timestamp=2026-05-01T01:30:00, risk_level=High, risk_score=5, reasons=['Access during leave', 'Access to unauthorized resource']

=== Session-level risk ===
user_id  session_id             session_start               session_end  duration_seconds  event_count  score risk_level                                                                       reasons
   u001           1 2026-05-04 14:48:02+00:00 2026-05-04 14:49:10+00:00              68.0            2      7       High night_time(+2), restricted_resource(+2), denied_once(+1), denied_multiple(+2)
   u002           0 2026-05-04 14:50:45+00:00 2026-05-04 14:54:27+00:00             222.0            3      5     Medium                                         night_time(+2), change_permission(+3)
   u001           0 2026-05-04 00:00:15+00:00 2026-05-04 00:05:33+00:00             318.0            3      0        Low
   u003           0 2026-05-04 01:15:00+00:00 2026-05-04 01:20:05+00:00             305.0            3      0        Low

=== User-level risk ===
user_id final_risk_level  total_score  session_count  high_session_count  medium_session_count  low_session_count
   u001             High            7              2                   1                     0                  1
   u002           Medium            5              1                   0                     1                  0
   u003              Low            0              1                   0                     0                  1

Markdown report generated: outputs/20260505_073903_insight_report.md
```

This sample reflects the verified Day8 state, combining event-level scoring with session-level and user-level risk aggregation and generating a single Markdown report that includes all three layers.

---

## Sample report output

A generated report includes summary statistics, detailed findings for Medium and High risk events, and Day7 session-level and user-level summaries.

Example:

```markdown
# Insight-Linker Risk Report

Generated at: 2026-05-05T07:39:03
Target period: 2026-05-01 to 2026-05-02 (sample data)
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

## Medium Risk Findings

### User u002 / 2026-05-01T02:15:00
- Risk level: Medium
- Risk score: 2
- Reasons: Access during leave

### User u001 / 2026-05-01T23:45:00
- Risk level: Medium
- Risk score: 3
- Reasons: After-hours access by resignation-notified user

## Session Risk Summary

- Total sessions: 4
- High risk sessions: 1
- Medium risk sessions: 1
- Low risk sessions: 2

### Session details

| user_id | session_id | risk_level | score | event_count | duration_seconds | session_start (UTC)        | session_end (UTC)          | reasons |
|--------|-----------:|-----------|------:|------------:|-----------------:|----------------------------|----------------------------|---------|
| u001 | 1 | High | 7 | 2 | 68 | 2026-05-04T14:48:02+00:00 | 2026-05-04T14:49:10+00:00 | night_time(+2), restricted_resource(+2), denied_once(+1), denied_multiple(+2) |
| u002 | 0 | Medium | 5 | 3 | 222 | 2026-05-04T14:50:45+00:00 | 2026-05-04T14:54:27+00:00 | night_time(+2), change_permission(+3) |
| u001 | 0 | Low | 0 | 3 | 318 | 2026-05-04T00:00:15+00:00 | 2026-05-04T00:05:33+00:00 | None |
| u003 | 0 | Low | 0 | 3 | 305 | 2026-05-04T01:15:00+00:00 | 2026-05-04T01:20:05+00:00 | None |

## User Risk Summary

- Total users in Day7 analysis: 3
- Users with final High risk: 1
- Users with final Medium risk: 1
- Users with final Low risk: 1

### User details

| user_id | final_risk_level | total_session_score | session_count | high_sessions | medium_sessions | low_sessions |
|--------|------------------|--------------------:|--------------:|--------------:|----------------:|-------------:|
| u001 | High | 7 | 2 | 1 | 0 | 1 |
| u002 | Medium | 5 | 1 | 0 | 1 | 0 |
| u003 | Low | 0 | 1 | 0 | 0 | 1 |

## Notes

- This report is generated from the current MVP scoring logic.
- Low risk events are counted in the summary but omitted from detailed event findings.
- Data in this report is sample data for MVP verification.
- Current event-level rules focus on leave status, resignation notice, and unauthorized resource access.
- Day7 session start/end timestamps are handled as UTC (sample CSV is stored in UTC).
- Event-level JSON and Day7 CSV are separate sample datasets used for different layers of the MVP.
- Day7 session-level and user-level analysis is included when sample log data is available.
```

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
- Day 7: Session-based scoring and user-level risk aggregation
- Day 8: Session-level and user-level risk tables embedded into the Markdown report

---

## Documentation

Additional Japanese design and implementation notes are available below:

- `docs/code_explanation_part1_ja.md` — Day3 input layer, models, loader, and sample JSON overview.
- `docs/code_explanation_part2_ja.md` — Day4 to Day5 scoring logic, report generation, and main flow updates.
- `docs/code_explanation_part3_ja.md` — Day6 to Day8 structured results, session analysis, and report integration.

---

## Possible next steps

Planned or possible future improvements include:

- Group findings by user in the event-level section.
- Handle missing HR or privilege context more explicitly.
- Enrich report formatting.
- Add tests.
- Add input validation.
- Support additional insider risk scenarios.

---

## Notes

- All data in this repository is sample data for MVP development.
- This is a learning and portfolio project, not a production-ready detection platform.
- Event-level and Day7 session-level analyses are intentionally based on separate sample datasets.
- Japanese code explanation notes can be maintained under `docs/` as supplementary design and learning records.

---

## License

MIT