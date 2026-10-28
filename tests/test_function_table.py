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


def evidence_path_problem(evidence, is_committed_file):
    """Return why an evidence path is unusable, or an empty string if it is fine."""
    file_part = evidence.split("#", 1)[0]
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
    if not is_committed_file(file_part):
        return f"evidence file {file_part!r} is not committed to the repository"
    return ""


def find_problems(text, is_committed_file):
    """Return (line number, problem) pairs for every rule the table text breaks.

    is_committed_file takes a repository-relative path and says whether git tracks
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

        if name.startswith("sub_"):
            if name != f"sub_{address}":
                problems.append((line_number, f"name {name!r} does not match address {address}"))
        elif confidence != "confirmed":
            problems.append((line_number, f"real name {name!r} needs confidence 'confirmed'"))
        elif not C_IDENTIFIER_PATTERN.fullmatch(name):
            problems.append((line_number, f"name {name!r} is not a C identifier"))
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
            path_problem = evidence_path_problem(evidence, is_committed_file)
            if path_problem:
                problems.append((line_number, path_problem))

        if purpose == "" or purpose != purpose.strip():
            problems.append((line_number, "purpose must be non-empty with no outer spaces"))
    return problems


def committed_files():
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
        committed = committed_files()
        problems = find_problems(text, lambda relative_path: relative_path in committed)
        report = "\n".join(f"line {number}: {problem}" for number, problem in problems)
        self.assertEqual(problems, [], f"{TABLE.name} has problems:\n{report}")

    def test_table_has_at_least_one_row(self):
        text = TABLE.read_bytes().decode("utf-8")
        self.assertGreater(len(text.splitlines()), 1)


class RuleTests(unittest.TestCase):
    GOOD_ROW = "00409ED0\tsub_00409ED0\tconfirmed\tdocs/proof.md\tReturns an address"

    @staticmethod
    def only_proof_is_committed(relative_path):
        return relative_path == "docs/proof.md"

    def problems_for(self, *rows):
        text = "\n".join([HEADER, *rows]) + "\n"
        return find_problems(text, self.only_proof_is_committed)

    def test_good_rows_pass(self):
        rows = [
            "0041B230\tsub_0041B230\tguess\tnone\tunknown",
            "00433F00\tsub_00433F00\tlikely\tdocs/proof.md#loading\tProbably loads weapons",
            "0045A1C0\tFireWeapon\tconfirmed\tdocs/proof.md\tFires the selected weapon group",
        ]
        self.assertEqual(self.problems_for(*rows), [])

    def test_each_broken_rule_is_reported(self):
        cases = {
            "four columns": "00409ED0\tsub_00409ED0\tconfirmed\tReturns an address",
            "lowercase address": "00409ed0\tsub_00409ed0\tguess\tnone\tunknown",
            "short address": "409ED0\tsub_409ED0\tguess\tnone\tunknown",
            "capital confidence": "00409ED0\tsub_00409ED0\tConfirmed\tdocs/proof.md\tunknown",
            "sub_ name for another address": "00409ED0\tsub_00409EE0\tguess\tnone\tunknown",
            "real name on a guess": "00409ED0\tPlaySound\tguess\tnone\tMaybe plays a sound",
            "real name with a space": "00409ED0\tFire Weapon\tconfirmed\tdocs/proof.md\tFires",
            "confirmed without evidence": "00409ED0\tsub_00409ED0\tconfirmed\tnone\tunknown",
            "evidence not committed": "00409ED0\tsub_00409ED0\tlikely\tdocs/missing.md\tunknown",
            "evidence outside the repo": "00409ED0\tsub_00409ED0\tlikely\t../proof.md\tunknown",
            "absolute evidence path": "00409ED0\tsub_00409ED0\tlikely\t/docs/proof.md\tunknown",
            "backslash evidence path": "00409ED0\tsub_00409ED0\tlikely\tdocs\\proof.md\tunknown",
            "dot-slash evidence path": "00409ED0\tsub_00409ED0\tlikely\t./docs/proof.md\tunknown",
            "empty purpose": "00409ED0\tsub_00409ED0\tguess\tnone\t",
            "purpose with outer spaces": "00409ED0\tsub_00409ED0\tguess\tnone\t unknown",
            "blank line": "",
        }
        # Each row breaks exactly one rule, so exactly one problem proves that rule fired.
        for label, row in cases.items():
            with self.subTest(label):
                self.assertEqual(len(self.problems_for(row)), 1)

    def test_rows_out_of_order_or_repeated_are_reported(self):
        later = "00433F00\tsub_00433F00\tguess\tnone\tunknown"
        earlier = "0041B230\tsub_0041B230\tguess\tnone\tunknown"
        self.assertEqual(len(self.problems_for(later, earlier)), 1)
        self.assertEqual(len(self.problems_for(earlier, earlier)), 1)

    def test_a_real_name_used_twice_is_reported(self):
        first = "0041B230\tFireWeapon\tconfirmed\tdocs/proof.md\tFires"
        second = "00433F00\tFireWeapon\tconfirmed\tdocs/proof.md\tFires"
        expected = [(3, "name 'FireWeapon' is already used on line 2")]
        self.assertEqual(self.problems_for(first, second), expected)

    def test_file_level_problems_are_reported(self):
        good_text = f"{HEADER}\n{self.GOOD_ROW}\n"
        bad_texts = {
            "wrong header": good_text.replace("purpose", "notes", 1),
            "CRLF endings": good_text.replace("\n", "\r\n"),
            "no final newline": good_text.removesuffix("\n"),
        }
        self.assertEqual(find_problems(good_text, self.only_proof_is_committed), [])
        for label, text in bad_texts.items():
            with self.subTest(label):
                self.assertNotEqual(find_problems(text, self.only_proof_is_committed), [])


if __name__ == "__main__":
    unittest.main()
