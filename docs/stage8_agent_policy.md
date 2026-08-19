# Stage 8 — Governed Agentic Workforce Planning Policy

## Product objective

Use aggregate model outputs to help HR plan department-level workforce actions. The agent may summarize a signal, select an intervention from an approved playbook, request human approval, and record the decision and outcome.

This is an educational simulation using the synthetic IBM HR dataset. It is not approved for operational employment decisions.

## Agent workflow

1. Read only aggregate, suppression-safe department output from Stage 6.
2. Check whether the department meets the reporting and review rules.
3. Describe the signal as a planning indicator, not a causal conclusion.
4. Select one or more options from the approved action playbook.
5. Submit the recommendation to an authorized HR reviewer.
6. Wait for an explicit approve, modify, or reject decision.
7. Create a simulated follow-up task only after approval.
8. Write an audit event containing the input version, rule result, recommendation, reviewer decision, timestamps, and eventual aggregate outcome.

## Allowed inputs

- Department
- Employees represented
- Aggregate high-risk count and rate
- Aggregate average predicted probability
- Reporting status
- Model version and decision threshold
- Approved operational context supplied for the department as a whole

Small or suppressed groups must never be passed to the agent.

## Prohibited inputs and uses

The agent must not:

- Read or reveal EmployeeNumber, names, email addresses, or individual risk scores.
- Create an individual employee profile or retention case.
- Use age, gender, marital status, disability, ethnicity, medical data, or another protected or highly sensitive attribute to recommend action.
- Recommend or execute hiring, termination, promotion, compensation, discipline, performance ratings, or other individual employment decisions.
- Claim that a model feature caused attrition.
- Contact employees or managers automatically.
- learn from reviewer outcomes automatically without a separate governed model-development process.

## Approved action playbook

The first simulation may recommend only department-wide, non-punitive actions:

| Action ID | Recommendation | Example evidence needed |
|---|---|---|
| WORKLOAD_REVIEW | Review aggregate workload and overtime patterns | Elevated department signal plus approved aggregate workload context |
| CAREER_PROGRAM | Offer a department-wide career-development or internal-mobility program | Elevated signal plus approved aggregate development context |
| MANAGER_LISTENING | Run a voluntary department listening session or anonymous pulse survey | Elevated signal with no reliable operational cause established |
| SCHEDULE_REVIEW | Review department scheduling practices | Elevated signal plus approved aggregate scheduling context |
| MONITOR_ONLY | Take no intervention; review the aggregate indicator next cycle | Signal below action threshold or evidence is insufficient |

The agent may explain why a playbook item fits the available aggregate context. It may not invent facts or recommend an action outside this table.

## Human approval gate

Every intervention other than `MONITOR_ONLY` requires an authorized HR reviewer to choose one of:

- `APPROVED`
- `MODIFIED`
- `REJECTED`

No task is created before that decision. A modification must remain within the approved playbook.

## Audit requirements

Each run must record:

- unique run ID
- timestamp
- model and policy versions
- aggregate input hash or snapshot reference
- department and reporting status
- triggered rule
- proposed playbook action and explanation
- reviewer decision and optional rationale
- final approved action
- follow-up status
- aggregate outcome when available
- errors or blocked-policy events

The audit log must exclude employee identifiers and individual predictions.

## Safety behavior

The workflow must stop and record a blocked-policy event when:

- required fields are missing
- the group is suppressed or too small
- an individual identifier or individual score is supplied
- a requested action falls outside the playbook
- reviewer approval is absent
- the input or model version cannot be established

## Success measures

Stage 8 will measure the workflow, not whether a particular employee stays:

- percentage of recommendations reviewed
- approval, modification, and rejection rates
- time from recommendation to review
- percentage of approved tasks completed
- policy-block rate
- completeness of audit records
- change in aggregate department indicators over later review cycles, interpreted cautiously

## Product Owner acceptance criteria

- Given a reported department aggregate, the agent returns only an approved playbook recommendation or `MONITOR_ONLY`.
- Given suppressed data or individual-level fields, the workflow blocks processing and writes an audit event.
- Given an unapproved recommendation, the workflow creates no follow-up task.
- Given approval, the workflow creates one simulated task and records traceability from signal to outcome.
- Every decision is reproducible from versioned rules and logged aggregate inputs.
