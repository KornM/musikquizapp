#!/usr/bin/env python3
"""
Script to check which of the 44 correctness properties have corresponding tests.
"""

import os
import re
from pathlib import Path

# All 44 properties from the design document
ALL_PROPERTIES = {
    1: "Global participant creation generates unique ID",
    2: "Participant profile storage",
    3: "Profile independence from sessions",
    4: "Authentication token generation",
    5: "Participant ID in response",
    6: "Profile retrieval",
    7: "Profile update persistence",
    8: "Profile updates propagate to sessions",
    9: "Auto-creation of session participation",
    10: "Participation record linkage",
    11: "Initial score is zero",
    12: "Join timestamp recording",
    13: "Complete participant list for session",
    14: "Participant list contains required fields",
    15: "Participant list reflects current profile",
    16: "Answer linked to participation",
    17: "Score isolation per session",
    18: "Independent participation records",
    19: "Scoreboard session specificity",
    20: "Score and answer persistence",
    21: "API response format compatibility",
    22: "Unauthorized access denial",
    23: "Token contains participant ID",
    24: "Unique tenant ID generation",
    25: "Tenant creation validation",
    26: "Tenant list completeness",
    27: "Tenant deletion blocks new sessions",
    28: "Tenant admin association",
    29: "Tenant admin creation validation",
    30: "Admin login returns tenant context",
    31: "Session inherits admin tenant",
    32: "Session list tenant filtering",
    33: "Cross-tenant session access denial",
    34: "Participant tenant association",
    35: "Cross-tenant session join denial",
    36: "Participant list tenant filtering",
    37: "Tenant form submission creates tenant",
    38: "Admin update persistence",
    39: "Admin deletion blocks access",
    40: "Password change effectiveness",
    41: "Admin tenant reassignment",
    42: "Query tenant isolation",
    43: "Tenant deletion cascades",
    44: "Participant deletion cascades",
}


def find_properties_in_tests():
    """Find which properties are tested in the test files."""
    test_dir = Path("tests/unit")
    covered_properties = set()

    for test_file in test_dir.glob("test_*_properties.py"):
        with open(test_file, "r") as f:
            content = f.read()
            # Look for "Property X:" patterns
            matches = re.findall(r"Property (\d+):", content)
            for match in matches:
                covered_properties.add(int(match))

    return covered_properties


def main():
    covered = find_properties_in_tests()
    missing = set(ALL_PROPERTIES.keys()) - covered

    print("=" * 80)
    print("PROPERTY-BASED TEST COVERAGE ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Properties: {len(ALL_PROPERTIES)}")
    print(f"Covered: {len(covered)}")
    print(f"Missing: {len(missing)}")
    print(f"Coverage: {len(covered) / len(ALL_PROPERTIES) * 100:.1f}%")

    if covered:
        print("\n" + "=" * 80)
        print("COVERED PROPERTIES:")
        print("=" * 80)
        for prop_num in sorted(covered):
            print(f"  ✓ Property {prop_num}: {ALL_PROPERTIES[prop_num]}")

    if missing:
        print("\n" + "=" * 80)
        print("MISSING PROPERTIES:")
        print("=" * 80)
        for prop_num in sorted(missing):
            print(f"  ✗ Property {prop_num}: {ALL_PROPERTIES[prop_num]}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
