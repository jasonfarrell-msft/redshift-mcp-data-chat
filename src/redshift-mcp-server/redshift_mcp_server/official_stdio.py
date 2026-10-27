"""Bound stdio frames before the MCP SDK parses the official child's output."""

import os
import signal
import subprocess
import sys
import threading

MAX_FRAME = 1024 * 1024


def main() -> None:
    child = subprocess.Popen(
        [os.environ["REDSHIFT_OFFICIAL_EXECUTABLE"]],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    assert child.stdin is not None and child.stdout is not None
    def interrupted(signum: int, frame: object) -> None:
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def forward_input() -> None:
        try:
            while line := sys.stdin.buffer.readline(MAX_FRAME + 1):
                if len(line) > MAX_FRAME:
                    break
                child.stdin.write(line)
                child.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            child.stdin.close()

    threading.Thread(target=forward_input, daemon=True).start()
    try:
        while line := child.stdout.readline(MAX_FRAME + 1):
            if len(line) > MAX_FRAME or not line.endswith(b"\n"):
                raise RuntimeError("Official MCP frame exceeded limit.")
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


if __name__ == "__main__":
    main()
