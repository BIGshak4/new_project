# Five design studies and question discovery

User-requested interactive comparison at `/design-lab`; standalone previews at `/design-preview?variant=studio|play|index|focus|trail`. These are proposals, not a replacement of the production design system. No proposal is selected or canonized.

## Direction contract

THESIS: let founders compare five complete task-oriented directions at realistic size, rather than color variations of one layout.

OWN-WORLD: Studio uses green/warm paper and a generous learning desk; Play uses lime and tactile logic inputs; Index uses burgundy and a typographic library; Focus uses restrained violet and adjacent question/answer workspaces; Trail uses apricot/forest and a navigable lesson path.

STORY: switch directions, inspect desktop or a genuine 390-pixel iframe viewport, try a search and a practice view, then choose a future production direction. No selection is written into the actual account.

FIRST VIEWPORT: a neutral comparison bar outside the preview, followed by one full-sized direction. Studio pairs an invitation with a live XOR experiment; Play leads with that experiment; Index leads with filters and question rows; Focus opens directly into solving; Trail leads with the next lesson in context.

FORM: five user-requested coded studies, not an approved replacement visual world. No concept-roll was run and no seed or external quality-bar card is claimed: these are five proposals before the user chooses a production direction. Shared demo content is explicitly labelled illustrative, including company tags and progress. The existing application's language and behavior remain intact.

FINISH: review the comparison and metadata/search extension; preserve existing design-system documents. Document any unverified surface honestly. No new production identity is approved by this task.

## Interaction and motion

All navigation, filters, question opening, answer entry, hint disclosure and submission confirmation operate locally within the demo. Submission never contacts an evaluator or persists an answer. XOR inputs calculate a real truth-table result. Its output animates once when changed; Trail nodes respond to hover. The gallery motion toggle and system reduced-motion preference disable these effects.

## Production discovery change

The library and question page show discipline, topic, detailed tags and company reports visibly. Missing company data is labelled as not yet reported, never invented. Source reports and candidate sightings are deduplicated for presentation only. A shared explanatory note replaces repeated unverified labels.

Search includes titles, topic names, discipline and known Hebrew/English company aliases, insensitive to case, Hebrew vowel marks, punctuation and spacing in the dedicated company filter. The alias list covers the current imported companies and can be extended for new ones; arbitrary unseen company transliterations are not automatically generated. Acquired companies such as Mellanox and NVIDIA remain separate reports.

## Verification

60 frontend tests passed, including four discovery tests. TypeScript and production build passed. On the deployed site, `אינטל`, `Intel`, `INTEL`, and `intel` returned the same 21 questions. The browser inspection also confirmed visible taxonomy/company metadata, the provenance explanation, and the 390px iframe layout. No stored question or company report was changed.

All five proposal directions were inspected at desktop size and in a genuine 390px iframe viewport, with local-only XOR, hints, search, and demo-submission interactions checked. The comparison includes an explicitly labelled option to view the real existing site; actions in that view retain normal production behavior.

The isolated finish review requested three changes: disclose the absent concept-roll/quality-bar evidence, remove two decorative eyebrows, and align the Trail connector. The verdict pass scored all three **resolved** and returned **ship**, scoped to those fixes rather than a new whole-surface approval. The documentation handoff preserved the incumbent system files and recorded the five studies as provisional.
