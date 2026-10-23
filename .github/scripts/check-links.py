# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail on a relative Markdown link whose target is not in the repository; docs/reviews is history."""
import os
import re
import subprocess
import sys

files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
tracked = set(files)
link = re.compile(r"\]\(([^)\s]+)\)")
broken = []
for f in (x for x in files if x.endswith(".md") and not x.startswith("docs/reviews/")):
    with open(f, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            for target in link.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                path = os.path.normpath(os.path.join(os.path.dirname(f), target.split("#")[0]))
                if path not in tracked and not any(t.startswith(path + "/") for t in tracked):
                    broken.append(f"{f}:{n}: {target}")
for b in broken:
    print(f"broken link: {b}", file=sys.stderr)
sys.exit(1 if broken else 0)
