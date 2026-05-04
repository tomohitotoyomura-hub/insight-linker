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
- Group Day7 sample logs into sessions and calculate session-level risk.
- Aggregate final user-level risk based on session outcomes.


---


## Example use case


A user accesses a sensitive file path:


- during leave
- after hours after a resignation notice
- outside their allowed resource scope


The tool scores the event and records the reasons behind the result so the outcome is not just a label, but an explainable finding.


The Day7 extension also looks at grouped activity over time, so suspicious behavior can be assessed not only as a single event, but also as a session pattern.


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
│  ├─ raw/
│  ├─ access_privileges.json
│  ├─ hr_context.json
│  ├─ user_activity.json
│  └─ day7_sample_logs.csv
│
├─ outputs/
│  └─ (generated) insight reports
│
├─ day7_analysis.py       # Session and user-level risk aggregation (Day7)
├─ requirements.txt
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


- `day7_analysis.py`  
  Standalone Day7 module that groups log events into 30-minute sessions, scores each session, and aggregates final user-level risk.


- `main.py`  
  Entry point that loads data, evaluates activities, prints results, runs Day7 analysis, and generates the report.


---


## Current scoring logic


The current MVP includes three explicit example rules:


- Access during leave
- After-hours access by a resignation-notified user
- Access to an unauthorized resource path


These rules are intentionally small and explicit so the project remains easy to understand and extend.


---


## Day7 session analysis


In addition to event-level scoring, the project now includes a Day7 analysis step that groups log events into user sessions and derives a higher-level risk view.


The goal is to move beyond isolated events and highlight risky behavior patterns across a session or across a user's recent activity.


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


For each user, the final risk level is based on the highest session risk observed across that user's sessions.


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


The core MVP logic is implemented in Python modules, while Day7 adds tabular session analysis on top of the event-level model.[file:279]


---


## Getting started


### 1. Clone the repository


```bash
git clone [https://github.com/tomohitotoyomura-hub/insight-linker.git](https://github.com/tomohitotoyomura-hub/insight-linker.git)
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


1. Load sample activity, HR, and privilege data from `data/raw/`
2. Evaluate each activity with the scoring engine
3. Print the event-level evaluation results to the console
4. Run Day7 session analysis on sample log data
5. Print session-level and user-level risk tables
6. Generate a Markdown report under `outputs/` with a timestamped filename


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

Markdown report generated: outputs/20260505_010238_insight_report.md
```


This sample reflects the verified Day7 state, combining event-level scoring with session-level and user-level risk aggregation.[file:279]


---


## Sample report output


A generated report includes summary statistics and detailed findings for Medium and High risk events.


Example:


```markdown
# Insight-Linker Risk Report


Generated at: 2026-05-05T01:02:38
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


At the current stage, Day7 session-level and user-level results are printed to the console and are not yet embedded into the generated Markdown report.[file:279]


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


---


## Possible next steps


Planned or possible future improvements include:


- Embed Day7 session and user summaries into the Markdown report
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