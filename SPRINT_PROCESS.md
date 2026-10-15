# Sprint Process

## Sprint Duration

2 weeks. Sprints start and end on Tuesdays.
Current sprint schedule is in the GitHub Milestones.

## Ceremonies

### Sprint Planning (Day 1, ~90 minutes)

Held at the start of every sprint. All three members required.

Agenda:

1. Review any incomplete tasks carried over from the previous sprint.
   Carry-overs go into the new sprint backlog immediately — do not
   re-estimate them, just reassign and move on.
2. Walk through the sprint's tasks. For each task:
   - Confirm the Definition of Done is clear.
   - Identify dependencies on other tasks in this sprint.
   - Assign one owner.
3. Flag any task that requires a spike (a technical unknown that needs
   investigation before implementation). A spike is timeboxed to 2 days
   and produces a written note in docs/spikes/, not working code.
4. Agree on sprint review date and time.

Output: every sprint task assigned to one owner, sprint milestone
attached in GitHub Projects, all tasks in "In Progress" column.

### Daily Standup (Every morning, async)

Post three lines in the team channel by 10:00 AM:

Done yesterday:
Doing today:
Blocked on:

If blocked, the blocker must be resolved the same day — either by the
team directly or escalated to the advisor. A blocker that sits for
more than one day becomes a sprint risk.

In-person or video sync twice per week (suggested: Wednesday and
Saturday) for anything that cannot be resolved in text.

### Sprint Review (Day 14, ~60 minutes)

Demonstrate what was built. Running code only — no slides describing
features, no "it almost works." Every completed task is shown live.

Attendees: all three members. Invite Dr. Daud Abdullah Asif every
second sprint (i.e., sprints 1, 3, 5, 7, 9).

Agenda:

1. Demo each completed task against the local OpenProject instance.
2. Show test results (pytest output, CI badge).
3. Record any task not completed and why.
4. Merge develop → main via the sprint PR if all sprint goals are met.
   If critical tasks are incomplete, do not merge — note the gap and
   carry tasks into the next sprint.

Advisor review format: prepare a 2-slide summary beforehand.
Slide 1: what was built this sprint, key metrics (test count,
latency numbers, accuracy figures if applicable).
Slide 2: one decision you need the advisor's input on.
Send slides to Dr. Daud 24 hours before the meeting.

### Sprint Retrospective (Day 14, immediately after review, ~30 min)

Three questions, written answers, committed to docs/retros/sprint-N.md:

1. What went well?
2. What slowed us down?
3. What do we change next sprint?

Retros are not optional. 30 minutes is the timebox. One action item
per retro maximum — agree on one concrete change and actually make it.

## Definition of Done

A task is Done when ALL of the following are true:

- Code merged to develop via an approved PR (minimum 1 approval).
- CI passes: lint, type check, all tests green.
- New unit or integration tests added for the feature. No feature
  ships without test coverage.
- CONTRACTS.md updated if the task changes any interface between
  components.
- ARCHITECTURE.md or docs/adr/ updated if the task involves an
  architectural decision.
- Feature demonstrated live at sprint review (or to one other
  team member synchronously before the review if the task was
  completed early).

"Almost done," "just needs cleanup," and "tests coming soon" are
not Done. The task stays In Review until every item above is checked.

## Task States in GitHub Projects

Backlog → exists, not yet started
In Progress → actively being worked on (max 2 tasks per person at once)
In Review → PR open, awaiting approval or CI result
Done → PR merged to develop, all DoD items confirmed

Move your task card yourself when its state changes. Do not wait
for someone else to update it.

## Handling Scope Changes from Advisors

When an advisor suggests a change or new requirement:

1. Do not start implementing it immediately.
2. Add it to the product backlog as a new issue with label
   type:feature or type:spike as appropriate.
3. Raise it at the next sprint planning.
4. Decide as a team: does it displace a committed task (carry that
   task to the next sprint), does it fit in the current sprint's
   remaining capacity, or does it go into a future sprint?

This protects the current sprint from uncontrolled scope changes.

## Spikes

A spike is used when a task has too much technical uncertainty to
estimate or implement directly.

Rules:

- Timeboxed to 2 days maximum.
- Output is a written note in docs/spikes/spike-N-title.md, not code.
- Note must contain: question investigated, approaches tried,
  conclusion, recommended next action.
- A spike result feeds directly into a follow-up implementation task
  in the same or next sprint.

Spikes are created as GitHub issues with label type:spike.
