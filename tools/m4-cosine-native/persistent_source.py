"""Carry compound cosine's reviewed finite numerical seam through full startup.

The literal source reconstruction consumes the current persistent BEFORE
machine. The original record supplies only exact input-domain checks and the
three observed F32 outputs plus x87 status/raw80 observations. Additional
current pages are preserved byte for byte, rather than read from an AFTER
record. The caller independently checks full State, CPU, pages and projection.
"""
from pathlib import Path
import importlib.util

SOURCE_PATH = Path(__file__).with_name('source_model.py')
spec = importlib.util.spec_from_file_location('compound_literal_source', SOURCE_PATH)
literal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(literal)

# This is the exact page order in the original fixed356992 record, whose
# BEFORE and AFTER memory blocks each contain43 whole pages.
ORIGINAL_PAGES = (
    0x5c8000, 0x5c9000, 0x5cb000, 0x5cc000, 0x5e0000, 0x5e1000,
    0x5e8000, 0x604000, 0x605000, 0x60b000, 0x20001000, 0x5bb000,
    0x780c1000, 0x78115000, 0x5e6000, 0x608000, 0x482000, 0x5ca000,
    0x5ed000, 0x5f4000, 0x603000, 0x606000, 0x609000, 0x638000,
    0x63c000, 0x63d000, 0x72c000, 0x730000, 0x9a1000, 0x5e4000,
    0x5e5000, 0x5e7000, 0x72b000, 0x731000, 0x5f498000, 0x736000,
    0x5f4cc000, 0x5bc000, 0x5cf000, 0x5fc000, 0x7810a000,
    0x78145000, 0x78146000,
)
assert len(ORIGINAL_PAGES) == len(set(ORIGINAL_PAGES)) == 43


def phase_goal(state_before, cpu_before, pages_before, original, contracts, pages):
    """Return source-derived phase goal and State using current carried inputs."""
    pages = tuple(pages)
    assert len(pages) == len(set(pages))
    assert set(ORIGINAL_PAGES) <= set(pages)
    assert len(pages_before) == len(pages) * 4096
    assert len(original) == 356992
    current = {
        page: pages_before[index * 4096:(index + 1) * 4096]
        for index, page in enumerate(pages)
    }
    fixed_before = b''.join(current[page] for page in ORIGINAL_PAGES)
    result = literal.derive(
        state_before, cpu_before, fixed_before, original, contracts, ORIGINAL_PAGES
    )
    fixed_after = result['pages']
    assert len(fixed_after) == 43 * 4096
    for index, page in enumerate(ORIGINAL_PAGES):
        current[page] = fixed_after[index * 4096:(index + 1) * 4096]
    goal = dict(
        after=result['CPU'],
        pages=b''.join(current[page] for page in pages),
        events=result['events'],
        numerical_oracle=result['numerical_oracle'],
        current_carried_BEFORE_machine=True,
        original_AFTER_machine_seed=False,
        complete_State_after_copy=False,
        extra_pages_preserved=sorted(set(pages) - set(ORIGINAL_PAGES)),
        undefined_AF_semantic_equality=False,
    )
    return goal, result['state']
