"""Retain the prior adapter's complete typed-contract module interface.

The frozen source bridge and capture adapter use B/NEW_CONTRACTS to recover
the inherited finite API schema. The additive ActualResponses class itself is
reused unchanged from responses.py.
"""
from responses import ActualResponses
import provider_responses_v2 as PRIOR
B=PRIOR.B
I=PRIOR.I
NEW_CONTRACTS=PRIOR.NEW_CONTRACTS
