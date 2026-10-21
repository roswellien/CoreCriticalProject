#!/usr/bin/env python3
"""Run a user-installed llvm-objdump against file-backed executable sections.

Output is private local research material. It is not a translated program and
does not establish function boundaries or separate inline data from instructions.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pe import PEError, PEImage, read_binary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument(
        "--output", type=Path, required=True, help="private local output, preferably under reports/"
    )
    parser.add_argument(
        "--llvm-objdump", default="llvm-objdump", help="path to a separately installed LLVM objdump"
    )
    parser.add_argument(
        "--timeout", type=int, default=60, help="subprocess time limit in seconds (1..600)"
    )
    args = parser.parse_args(argv)
    temporary: Path | None = None
    try:
        if not 1 <= args.timeout <= 600:
            raise ValueError("timeout must be between 1 and 600 seconds")
        if args.output.resolve() == args.binary.resolve():
            raise ValueError("output must differ from the input binary")
        image = PEImage(read_binary(args.binary))
        sections = [
            section["name"]
            for section in image.sections
            if section["executable"] and section["raw_size"]
        ]
        if not sections:
            raise PEError("no file-backed executable sections")
        if any(
            not name or not name.isascii() or any(ord(character) < 32 for character in name)
            for name in sections
        ):
            raise PEError("section names cannot safely be passed to llvm-objdump")
        executable = shutil.which(args.llvm_objdump)
        if not executable:
            raise ValueError(
                "llvm-objdump is unavailable; install LLVM separately or pass --llvm-objdump"
            )
        command = [executable, "--disassemble", "--no-show-raw-insn", "--x86-asm-syntax=intel"]
        command.extend(f"--section={name}" for name in sections)
        # LLVM 21 objdump does not accept a standalone option terminator.
        # An absolute path cannot be mistaken for a leading-dash option.
        command.append(str(args.binary.resolve()))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=args.output.parent, prefix="disassembly-", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(
                b"PRIVATE LOCAL RESEARCH: unverified linear disassembly, not function recovery.\n"
            )
            stream.flush()
            completed = subprocess.run(
                command, stdout=stream, stderr=subprocess.PIPE, timeout=args.timeout, check=False
            )
        if completed.returncode:
            detail = completed.stderr.decode("utf-8", errors="replace")[:4096]
            raise ValueError(f"llvm-objdump exited with {completed.returncode}: {detail}")
        os.replace(temporary, args.output)
        temporary = None
        print(
            f"Private disassembly written to {args.output}; instructions and boundaries require manual verification."
        )
        return 0
    except (PEError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"disassembly failed: {error}", file=sys.stderr)
        return 3
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
