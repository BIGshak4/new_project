# Question source screenshots: learner display removal

At Harel's request, the 50 archived screenshots under `interview_preparation/sources/`
are no longer displayed or linked from question or solution resource panels.

- The frontend blocks the existing filenames, including screenshots previously
  classified as solution/reference material, so an older API response cannot render them.
- The backend excludes `sources/` records before generating learner-facing signed
  URLs. This applies to existing database manifests without a reseed.
- Authored illustrations under `diagrams/`, solution code, question text, categories,
  reported companies, answers and learner history remain intact.
- The private archive and provenance records are retained. This is a publication
  boundary, not an assertion of ownership or permission to reuse third-party material.
- Previously issued private links expire under the existing 30-minute signing policy;
  this change does not revoke those links early or delete the archived storage objects.

Question diagrams that exist only inside screenshots should be replaced with original
standalone illustrations before wider publication. The existing internal grading
image context is unchanged by this display-only change.
