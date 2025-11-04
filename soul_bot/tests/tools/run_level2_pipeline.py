#!/usr/bin/env python3
"""Helper script to run Level 2 validation tests locally."""

import subprocess
import sys


def main() -> int:
    command = ['pytest',
               'tests/unit/test_personalize_response.py',
               'tests/smoke_tests.py::TestLevel2ContextualExamples']

    print('🔁 Running Level 2 validation suite...', flush=True)
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())

