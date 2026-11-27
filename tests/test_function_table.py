"""Checks that games/mw3/symbols/functions.tsv follows the format its README describes.

The table will grow to thousands of rows written by many people and agents, so these
checks keep it readable by tools and keep the naming rule from CODE_STYLE.md: a
function keeps its sub_XXXXXXXX name until it is confirmed, and a confirmed row points
at its evidence.
"""

import re
import subprocess
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "games/mw3/symbols/functions.tsv"

HEADER = "address\tname\tconfidence\tevidence\tpurpose"
COLUMN_COUNT = 5
CONFIDENCE_WORDS = ("guess", "likely", "confirmed")
ADDRESS_PATTERN = re.compile(r"[0-9A-F]{8}")
C_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# C89/C99 keywords plus common C/C++ keywords that cannot be used as function names.
RESERVED_C_KEYWORDS = frozenset({
    # C89 keywords
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
    # C99 keywords
    "inline", "restrict", "_Bool", "_Complex", "_Imaginary",
    # Additional C/C++ keywords
    "bool", "true", "false", "class", "new", "delete", "this",
})

# Characters that break spreadsheet formulas or get stripped by CSV readers when at index 0.
FORBIDDEN_PURPOSE_PREFIXES = ('"', "=", "+", "-", "@")


def evidence_path_problem(evidence, is_tracked_file):
    """Return why an evidence path is unusable, or an empty string if it is fine."""
    if "#" in evidence:
        file_part, heading = evidence.split("#", 1)
        if not heading:
            return f"evidence {evidence!r} has an empty anchor after '#'"
    else:
        file_part = evidence
    path = PurePosixPath(file_part)
    # Git lists paths in one exact spelling, so "./a/b" or "a//b" would never match it.
    is_plain_relative_path = (
        file_part != ""
        and str(path) == file_part
        and "\\" not in file_part
        and ":" not in file_part
        and not path.is_absolute()
        and ".." not in path.parts
    )
    if not is_plain_relative_path:
        return f"evidence {evidence!r} is not a forward-slash path inside the repository"
    if not is_tracked_file(file_part):
        return f"evidence file {file_part!r} is not tracked in the repository"
    return ""


def find_problems(text, is_tracked_file):
    """Return (line number, problem) pairs for every rule the table text breaks.

    is_tracked_file takes a repository-relative path and says whether git tracks
    that file, so tests can check made-up rows without real evidence files.
    """
    problems = []
    if "\r" in text:
        problems.append((0, "file has CR characters; use LF line endings"))
    if not text.endswith("\n"):
        problems.append((0, "file must end with a newline"))
    lines = text.removesuffix("\n").split("\n")
    if lines[0] != HEADER:
        problems.append((1, f"header must be {HEADER!r}"))

    previous_address = ""
    previous_address_line = 0
    descriptive_name_lines = {}
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        if len(fields) != COLUMN_COUNT:
            problems.append((line_number, f"expected {COLUMN_COUNT} tab-separated columns"))
            continue
        address, name, confidence, evidence, purpose = fields

        if ADDRESS_PATTERN.fullmatch(address):
            if previous_address and address <= previous_address:
                order_problem = (
                    f"address {address} must come after {previous_address} "
                    f"on line {previous_address_line}"
                )
                problems.append((line_number, order_problem))
            previous_address = address
            previous_address_line = line_number
        else:
            problems.append((line_number, f"address {address!r} is not 8 uppercase hex digits"))

        if confidence not in CONFIDENCE_WORDS:
            problems.append(
                (line_number, f"confidence {confidence!r} is not one of {CONFIDENCE_WORDS}")
            )

        if name.lower().startswith("sub_"):
            if name != f"sub_{address}":
                problems.append((line_number, f"name {name!r} does not match address {address}"))
        elif confidence != "confirmed":
            problems.append((line_number, f"real name {name!r} needs confidence 'confirmed'"))
        elif not C_IDENTIFIER_PATTERN.fullmatch(name):
            problems.append((line_number, f"name {name!r} is not a C identifier"))
        elif name in RESERVED_C_KEYWORDS:
            problems.append((line_number, f"name {name!r} is a reserved C/C++ keyword"))
        elif name in descriptive_name_lines:
            first_use_line = descriptive_name_lines[name]
            reuse_problem = f"name {name!r} is already used on line {first_use_line}"
            problems.append((line_number, reuse_problem))
        else:
            descriptive_name_lines[name] = line_number

        if evidence == "none":
            if confidence == "confirmed":
                problems.append((line_number, "a confirmed row must name its evidence file"))
        else:
            path_problem = evidence_path_problem(evidence, is_tracked_file)
            if path_problem:
                problems.append((line_number, path_problem))

        if purpose == "" or purpose != purpose.strip():
            problems.append((line_number, "purpose must be non-empty with no outer spaces"))
        elif purpose.startswith(FORBIDDEN_PURPOSE_PREFIXES):
            formula_problem = (
                f"purpose cannot start with {purpose[0]!r} (formula or quote character)"
            )
            problems.append((line_number, formula_problem))
    return problems


def tracked_files():
    """List the files git tracks.

    Evidence must be something every contributor and CI can read. A local-only file,
    such as a private report under the git-ignored reports/ folder, exists on one PC
    but not in the repository, so checking the disk would pass there and fail on CI.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return set(listing.split("\0")) - {""}


class RealTableTests(unittest.TestCase):
    def test_table_follows_every_rule(self):
        text = TABLE.read_bytes().decode("utf-8")
        tracked = tracked_files()
        problems = find_problems(text, lambda relative_path: relative_path in tracked)
        report = "\n".join(f"line {number}: {problem}" for number, problem in problems)
        self.assertEqual(problems, [], f"{TABLE.name} has problems:\n{report}")

    def test_table_has_at_least_one_row(self):
        text = TABLE.read_bytes().decode("utf-8")
        self.assertGreater(len(text.splitlines()), 1)


class RuleTests(unittest.TestCase):
    GOOD_ROW = "00409ED0\tsub_00409ED0\tconfirmed\tdocs/proof.md\tReturns an address"

    @staticmethod
    def only_proof_is_tracked(relative_path):
        return relative_path == "docs/proof.md"

    def problems_for(self, *rows):
        text = "\n".join([HEADER, *rows]) + "\n"
        return find_problems(text, self.only_proof_is_tracked)

    def test_good_rows_pass(self):
        rows = [
            "0041B230\tsub_0041B230\tguess\tnone\tunknown",
            "00433F00\tsub_00433F00\tlikely\tdocs/proof.md#loading\tProbably loads weapons",
            "0045A1C0\tFireWeapon\tconfirmed\tdocs/proof.md\tFires the selected weapon group",
        ]
        self.assertEqual(self.problems_for(*rows), [])

    def test_each_broken_rule_is_reported(self):
        cases = {
            "four columns": (
                "00409ED0\tsub_00409ED0\tconfirmed\tReturns an address",
                "columns",
            ),
            "lowercase address": (
                "00409ed0\tsub_00409ed0\tguess\tnone\tunknown",
                "uppercase hex",
            ),
            "short address": (
                "409ED0\tsub_409ED0\tguess\tnone\tunknown",
                "uppercase hex",
            ),
            "capital confidence": (
                "00409ED0\tsub_00409ED0\tConfirmed\tdocs/proof.md\tunknown",
                "confidence",
            ),
            "sub_ name for another address": (
                "00409ED0\tsub_00409EE0\tguess\tnone\tunknown",
                "match",
            ),
            "uppercase sub_ name": (
                "00409ED0\tSUB_00409ED0\tconfirmed\tdocs/proof.md\tReturns an address",
                "match",
            ),
            "real name on a guess": (
                "00409ED0\tPlaySound\tguess\tnone\tMaybe plays a sound",
                "confirmed",
            ),
            "real name with a space": (
                "00409ED0\tFire Weapon\tconfirmed\tdocs/proof.md\tFires",
                "identifier",
            ),
            "C keyword name": (
                "00409ED0\tint\tconfirmed\tdocs/proof.md\tReturns an address",
                "keyword",
            ),
            "confirmed without evidence": (
                "00409ED0\tsub_00409ED0\tconfirmed\tnone\tunknown",
                "evidence",
            ),
            "evidence not tracked": (
                "00409ED0\tsub_00409ED0\tlikely\tdocs/missing.md\tunknown",
                "tracked",
            ),
            "evidence outside the repo": (
                "00409ED0\tsub_00409ED0\tlikely\t../proof.md\tunknown",
                "forward-slash",
            ),
            "absolute evidence path": (
                "00409ED0\tsub_00409ED0\tlikely\t/docs/proof.md\tunknown",
                "forward-slash",
            ),
            "backslash evidence path": (
                "00409ED0\tsub_00409ED0\tlikely\tdocs\\proof.md\tunknown",
                "forward-slash",
            ),
            "dot-slash evidence path": (
                "00409ED0\tsub_00409ED0\tlikely\t./docs/proof.md\tunknown",
                "forward-slash",
            ),
            "empty evidence anchor": (
                "00409ED0\tsub_00409ED0\tlikely\tdocs/proof.md#\tunknown",
                "anchor",
            ),
            "empty purpose": (
                "00409ED0\tsub_00409ED0\tguess\tnone\t",
                "empty",
            ),
            "purpose with outer spaces": (
                "00409ED0\tsub_00409ED0\tguess\tnone\t unknown",
                "spaces",
            ),
            "purpose starting with formula": (
                "00409ED0\tsub_00409ED0\tguess\tnone\t=SUM(A1)",
                "formula",
            ),
            "purpose starting with quote": (
                "00409ED0\tsub_00409ED0\tguess\tnone\t\"quoted\"",
                "quote",
            ),
            "blank line": (
                "",
                "columns",
            ),
        }
        # Each row breaks exactly one rule, so exactly one problem proves that rule fired.
        for label, (row, expected_word) in cases.items():
            with self.subTest(label):
                problems = self.problems_for(row)
                self.assertEqual(len(problems), 1)
                self.assertIn(expected_word, problems[0][1])

    def test_rows_out_of_order_or_repeated_are_reported(self):
        later = "00433F00\tsub_00433F00\tguess\tnone\tunknown"
        earlier = "0041B230\tsub_0041B230\tguess\tnone\tunknown"
        later_then_earlier = self.problems_for(later, earlier)
        self.assertEqual(len(later_then_earlier), 1)
        self.assertIn("must come after", later_then_earlier[0][1])
        repeated = self.problems_for(earlier, earlier)
        self.assertEqual(len(repeated), 1)
        self.assertIn("must come after", repeated[0][1])

    def test_a_real_name_used_twice_is_reported(self):
        first = "0041B230\tFireWeapon\tconfirmed\tdocs/proof.md\tFires"
        second = "00433F00\tFireWeapon\tconfirmed\tdocs/proof.md\tFires"
        expected = [(3, "name 'FireWeapon' is already used on line 2")]
        self.assertEqual(self.problems_for(first, second), expected)

    def test_file_level_problems_are_reported(self):
        good_text = f"{HEADER}\n{self.GOOD_ROW}\n"
        bad_texts = {
            "wrong header": (good_text.replace("purpose", "notes", 1), "header"),
            "CRLF endings": (good_text.replace("\n", "\r\n"), "CR"),
            "no final newline": (good_text.removesuffix("\n"), "newline"),
        }
        self.assertEqual(find_problems(good_text, self.only_proof_is_tracked), [])
        for label, (text, expected_word) in bad_texts.items():
            with self.subTest(label):
                problems = find_problems(text, self.only_proof_is_tracked)
                self.assertNotEqual(problems, [])
                self.assertIn(expected_word, problems[0][1])


if __name__ == "__main__":
    unittest.main()
