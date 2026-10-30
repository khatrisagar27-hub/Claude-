"""
Statutory reference layer — every legal threshold, rate and section number the
rules and engines use lives here, with the date it took effect and its source.

Nothing in app/rules or app/engines should hard-code a statutory figure; import it
from this package instead so a change in law is a one-line, dated edit.

Sources were verified against the bare text on the dates noted in each module.
Thresholds move — re-verify before relying on an output in a signed deliverable.
"""
