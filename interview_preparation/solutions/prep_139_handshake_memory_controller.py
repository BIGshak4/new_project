"""One-entry, globally serialized memory controller (cycle-accurate logical model)."""


class Controller:
    """Two stable-valid request ports; completion means operation has committed.

    ``step`` returns signals sampled at this edge, then changes the state.
    A read/write request is (address, data); read data is ignored at acceptance.
    Completion may coincide with backend acceptance. Responses are retained
    until consumed. Initial state is empty; resetting an outstanding transaction
    requires a separate whole-system cancellation contract.
    """

    def __init__(self):
        self.state = "IDLE"
        self.priority = "R"
        self.pending = None
        self.result = None

    def step(self, read=None, write=None, *, command_ready=False, completion=None, response_ready=False):
        # completion = ("R", read_data) or ("W", None)
        out = {"read_ready": False, "write_ready": False, "command": None, "response": None, "accepted": None}
        if self.state == "IDLE":
            if completion is not None:
                raise ValueError("Unsolicited completion")
            op = (
                self.priority
                if read is not None and write is not None
                else "R"
                if read is not None
                else "W"
                if write is not None
                else None
            )
            if op is not None:
                address, data = read if op == "R" else write
                self.pending = (op, address, data if op == "W" else None)
                out["read_ready" if op == "R" else "write_ready"] = True
                out["accepted"] = self.pending
                self.priority = "W" if op == "R" else "R"
                self.state = "ISSUE"
        elif self.state == "ISSUE":
            out["command"] = self.pending
            if completion is not None and not command_ready:
                raise ValueError("Completion before command acceptance")
            if command_ready:
                self.state = "WAIT"
                if completion is not None:
                    self._complete(completion)
        elif self.state == "WAIT":
            if completion is not None:
                self._complete(completion)
        elif self.state == "RESP":
            if completion is not None:
                raise ValueError("Repeated completion")
            out["response"] = self.result
            if response_ready:
                self.pending = self.result = None
                self.state = "IDLE"
        return out

    def _complete(self, completion):
        if completion[0] != self.pending[0]:
            raise ValueError("Completion does not match outstanding operation")
        self.result = completion
        self.state = "RESP"
