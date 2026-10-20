import assert from "node:assert/strict";
import test from "node:test";
import {
  SUPPORT_LIMITS, inspectSupportFile, inspectSupportFiles, removeSupportReservation, sendSupportReport, supportPageContext,
  supportErrorMessage, SupportValidationError, validateSupportDetails,
  type SupportFile, type SupportSubmission, type SupportTransport,
} from "../src/lib/support-report";

const input: SupportSubmission = { id: "stable-report-id", subject: "Circuit not saved", description: "I connected two gates but saving did not complete.", category: "bug", language: "en", pagePath: "/", questionKey: "example-enabled-decoder" };
const sample = (name = "example.txt", content: BlobPart = "A valid support attachment.", type = "text/plain") => new File([content], name, { type });
const item = (id: string): SupportFile => ({ id, file: sample(), mimeType: "text/plain", uploaded: false });

test("support accepts signatures for each supported binary format and UTF-8 text", async () => {
  const examples = [
    sample("a.png", new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]), "image/png"),
    sample("b.jpg", new Uint8Array([255, 216, 255, 225]), "image/jpeg"),
    sample("c.webp", "RIFF1234WEBPdata", "image/webp"),
    sample("d.pdf", "%PDF-1.7\n", "application/pdf"),
    sample("e.txt", "שלום, נתקלתי בבעיה."),
  ];
  assert.deepEqual(await inspectSupportFiles(examples), ["image/png", "image/jpeg", "image/webp", "application/pdf", "text/plain"]);
  assert.equal(await inspectSupportFile(sample("UNKNOWN.JPG", new Uint8Array([255, 216, 255]), "")), "image/jpeg");
});

test("support rejects executable/vector/office formats, renamed images and declared MIME mismatches", async () => {
  for (const file of [sample("a.svg"), sample("a.docx"), sample("a.exe"), sample("a.html"), sample("a.jpg", "text", "image/jpeg"), sample("a.png", "%PDF-1.7", "application/pdf")]) {
    await assert.rejects(() => inspectSupportFile(file), SupportValidationError);
  }
});

test("plain text cannot hide null bytes or invalid UTF-8", async () => {
  for (const bytes of [new Uint8Array([65, 0, 66]), new Uint8Array([0xc3, 0x28])]) {
    await assert.rejects(() => inspectSupportFile(sample("binary.txt", bytes)), error => error instanceof SupportValidationError && error.code === "file_contents");
  }
});

test("attachment filenames cannot include paths, controls or unbounded display text", async () => {
  for (const name of ["../secret.txt", "folder\\secret.txt", "\u202eexample.txt", `${"a".repeat(181)}.txt`, "a\n.txt"]) {
    await assert.rejects(() => inspectSupportFile(sample(name)), { code: "file_name" });
  }
  assert.equal(await inspectSupportFile(sample("תיאור הבעיה.txt")), "text/plain");
});

test("file count, per-file, empty and aggregate limits are checked before upload", async () => {
  await assert.rejects(() => inspectSupportFiles(Array.from({ length: 6 }, () => sample())), { code: "file_count" });
  await assert.rejects(() => inspectSupportFile(sample("empty.txt", "")), { code: "file_size" });
  await assert.rejects(() => inspectSupportFile(sample("big.txt", new Uint8Array(SUPPORT_LIMITS.fileBytes + 1))), { code: "file_size" });
  const maximum = sample("a.txt", new Uint8Array(SUPPORT_LIMITS.fileBytes));
  await assert.rejects(() => inspectSupportFiles([maximum, maximum, maximum, maximum]), { code: "total_size" });
});

test("report subject and description validation trim whitespace and bound useful content", () => {
  assert.throws(() => validateSupportDetails("  ", input.description), { code: "subject" });
  assert.throws(() => validateSupportDetails(input.subject, "123"), { code: "description" });
  assert.throws(() => validateSupportDetails("a".repeat(161), input.description), { code: "subject" });
  assert.doesNotThrow(() => validateSupportDetails(input.subject, input.description));
});

test("support context never includes credentials, unknown paths, hashes or unrelated query parameters", () => {
  assert.deepEqual(supportPageContext("https://site.test/?question=example-enabled-decoder&access_token=secret#password=secret"), { pagePath: "/", questionKey: "example-enabled-decoder" });
  assert.deepEqual(supportPageContext("https://site.test/tour?email=private@example.com"), { pagePath: "/tour", questionKey: null });
  assert.deepEqual(supportPageContext("https://site.test/reset/secret-token?question=%3Cscript%3E"), { pagePath: "/", questionKey: null });
  assert.deepEqual(supportPageContext("not a URL"), { pagePath: "/", questionKey: null });
});

test("partial file failures preserve the saved report and retry only failed uploads", async () => {
  const saved: string[] = [], uploaded: string[] = [], removed: string[] = [];
  let fail = true;
  const transport: SupportTransport = {
    async saveReport(report) { saved.push(report.id); },
    async reserveFile(_reportId, file) { return `owner/report/${file.id}`; },
    async uploadFile(_path, file) { uploaded.push(file.id); if (fail && file.id === "second") throw new Error("temporary network error"); },
    async removeReservation(id) { removed.push(id); },
  };
  const first = await sendSupportReport(transport, input, [item("first"), item("second")]);
  assert.equal(first.reportSaved, true);
  assert.equal(first.failedFiles, 1);
  assert.deepEqual(first.files.map(file => file.uploaded), [true, false]);
  fail = false;
  const retry = await sendSupportReport(transport, input, first.files, { alreadySaved: first.reportSaved });
  assert.equal(retry.failedFiles, 0);
  assert.deepEqual(saved, [input.id]);
  assert.deepEqual(uploaded, ["first", "second", "second"]);
  assert.deepEqual(removed, ["second"]);
});

test("an uncertain report response can retry the same ID without beginning attachment uploads", async () => {
  const ids: string[] = [];
  let uploads = 0, attempt = 0;
  const transport: SupportTransport = {
    async saveReport(report) { ids.push(report.id); if (++attempt === 1) throw new Error("lost response"); },
    async reserveFile(_reportId, file) { return file.id; },
    async uploadFile() { uploads++; },
    async removeReservation() {},
  };
  const failed = await sendSupportReport(transport, input, [item("first")]);
  assert.equal(failed.reportSaved, false);
  assert.equal(uploads, 0);
  await sendSupportReport(transport, input, failed.files);
  assert.deepEqual(ids, [input.id, input.id]);
  assert.equal(uploads, 1);
});

test("switching accounts stops remaining uploads and prevents stale progress publishing", async () => {
  let current = true, uploads = 0, updates = 0;
  const transport: SupportTransport = {
    async saveReport() {},
    async reserveFile(_report, file) { current = false; return file.id; },
    async uploadFile() { uploads++; },
    async removeReservation() {},
  };
  await sendSupportReport(transport, input, [item("first"), item("second")], { isCurrent: () => current, onProgress: () => updates++ });
  assert.equal(uploads, 0);
  assert.equal(updates, 0);
});

test("finishing a saved report after omitting failed files does not save a duplicate", async () => {
  let saves = 0;
  const transport: SupportTransport = { async saveReport() { saves++; }, async reserveFile() { throw new Error("unused"); }, async uploadFile() {}, async removeReservation() {} };
  const result = await sendSupportReport(transport, input, [], { alreadySaved: true });
  assert.equal(result.reportSaved, true);
  assert.equal(result.failedFiles, 0);
  assert.equal(saves, 0);
});

test("a server-refused omission cannot disappear from the local pending attachment list", async () => {
  const original = [item("persisted-upload")];
  let remaining = [...original];
  await assert.rejects(async () => {
    await removeSupportReservation(async () => ({ data: false, error: null }));
    remaining = remaining.filter(file => file.id !== original[0].id);
  }, /not confirmed/);
  assert.deepEqual(remaining, original);
  await removeSupportReservation(async () => ({ data: true, error: null }));
  remaining = remaining.filter(file => file.id !== original[0].id);
  assert.equal(remaining.length, 0);
  await assert.rejects(() => removeSupportReservation(async () => ({ data: null, error: null })), /not confirmed/);
  await assert.rejects(() => removeSupportReservation(async () => ({ data: "true", error: null })), /not confirmed/);
  const rpcError = new Error("network response lost");
  await assert.rejects(() => removeSupportReservation(async () => ({ data: true, error: rpcError })), rpcError);
});

test("public-facing error copy never leaks raw database or provider details", () => {
  const error = { message: "database password=super-secret detail" };
  assert.ok(!supportErrorMessage(error, true).includes("super-secret"));
  assert.ok(supportErrorMessage({ message: "daily report limit exceeded" }, false).includes("daily limit"));
});
