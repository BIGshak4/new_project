// Developer-reviewed regression payload. It creates only its own scratch
// symlinks and attempts writes to this job's disposable control files. It never
// opens an application secret, credential, external endpoint or other user data.
export const CONTROL_TAMPER_FIXTURE = {
  language: "python",
  source: `def control_probe(n):
    import os
    control = "/vercel/sandbox/jobrun-control"
    for name in ("process_runner.py", "function.py", "solution.py", "args-0.json", "command-0.json"):
        try:
            with open(control + "/" + name, "w") as f:
                f.write("unexpected-control-write")
        except PermissionError:
            pass
        else:
            raise RuntimeError("Control file was writable: " + name)
    if n == 0:
        for name in ("command-2.json", "args-1.json"):
            path = "/vercel/sandbox/job/" + name
            if os.path.lexists(path):
                os.unlink(path)
            os.symlink(control + "/process_runner.py", path)
    return n
`,
  stdin: "",
  spec: { kind: "function", entry: "control_probe", cases: [{ args: [0], expected: 0 }, { args: [1], expected: 1 }] },
};
