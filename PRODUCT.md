# JobRun
<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
Israeli electrical/electronics students and junior candidates preparing for technical interviews. Harel Artman and Shaked Bozi operate a separate private task board.

## Product Purpose
Make deliberate interview practice approachable in Hebrew and English. Give founders a reliable shared place for tasks, decisions, subtasks, and progress.

## Stack
Existing Next.js App Router, React, TypeScript, Supabase, and user-selected Netlify hosting. Separate applications in apps/web and apps/tasks.

## Capabilities and Constraints
Initial delivery: bilingual question library, written practice, hints, reference solutions and personal practice history; private founder task CRUD, filters, assignments, subtasks, comments, and conflict-safe saves. Supabase Auth and database authorization protect personal and internal data. Existing schema and Shaked's work must be preserved. AI evaluations need an actual provider and validated integration; do not fabricate them. Current repository has 30 original bilingual review questions, not 150 approved questions. Company provenance and expert approval must never be invented.

## Brand Commitments
JobRun is a working name. Hebrew-first, complete English switching for the interview app, familiar English engineering terminology, responsive and professionally designed. On 2026-10-01 the founders selected adaptive Ion for the production practice site: cream/deep-purple light mode by default (updated by the user on 2026-10-02), violet dark mode on demand, preserving the real backend workflows. This selection supersedes earlier visual assumptions for the practice site; the separate task app keeps its existing design.

## Operating Context
Two founders collaborate asynchronously. Online previews and manual deployments precede GitHub integration, which needs the repository owner's authorization. Netlify currently has a Free team; no paid upgrade is authorized automatically.

## Evidence on Hand
example_question/questions.json contains 30 AI-assisted original questions marked in_review. The separate verify_example_questions bank is not approved for publication. src/ contains the long-term product specifications. C:/Projects/Job_Run/task-board-build-brief.md supplies task features, not authority to weaken security.

## Product Principles
Keep real progress distinct from self-assessment. Preserve unsaved text and prevent concurrent overwrites. Make current capabilities explicit. Keep internal work private.

## Open Decisions and Assumptions
The original daylight/green visual assumption is superseded by the explicit adaptive Ion choice above. No general workflow preference is inferred. Earlier infrastructure and content inventories in this file describe the initial delivery; consult current deployment and handoff documents before using them as operational facts.
