"""Register this environment's Python as the Jupyter kernel the workshop notebooks ask for.

The notebooks name the kernel `agentic-memory`, not `python3`: a `python3` kernelspec in the
user's Jupyter directory (left by another project or a deleted virtualenv) takes precedence
over the one inside `.venv`, so the labs would start in the wrong Python or not at all.
The spec is written inside `.venv` (`--sys-prefix`), so it never touches other projects.

`workshop-kernel --user` writes the same spec to the user's Jupyter directory instead. The
Codespace runs it too (the container holds only this project): VS Code then finds a kernel that
matches the notebooks' kernelspec exactly and selects it, so Run All works without a prompt.
"""

from __future__ import annotations

import sys

from . import use_utf8_output

KERNEL_NAME = "agentic-memory"
DISPLAY_NAME = "Python (agentic-memory workshop)"


def main(argv: list[str] | None = None) -> int:
    use_utf8_output()
    from ipykernel.kernelspec import install

    user = "--user" in (sys.argv[1:] if argv is None else argv)
    path = install(
        kernel_name=KERNEL_NAME,
        display_name=DISPLAY_NAME,
        user=user,
        prefix=None if user else sys.prefix,
    )
    print(f"✓ Jupyter kernel '{KERNEL_NAME}' -> {sys.executable}")
    print(f"  spec: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
