#! /bin/sh
""":"
exec python "$0" ${1+"$@"}
"""

__doc__ = """The above defines the script's __doc__ string. You can fix it by like this."""

import re
import sys
import ngnrouterlib

patternfile = sys.argv[1]
targetfile = sys.argv[2]

if (ngnrouterlib.checkre(patternfile, targetfile)):
    print("True")
else:
    print("False")
