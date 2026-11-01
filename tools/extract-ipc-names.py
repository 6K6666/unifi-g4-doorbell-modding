#!/usr/bin/env python3
"""List the IPC message names found in copies of the doorbell's service binaries.

Usage: tools/extract-ipc-names.py BINARY [BINARY ...] > ipc-names.txt

Names only, from `strings`-style scanning: a name in a binary does not show that the service handles it
on your board. Binaries that are shell scripts or contain no names are skipped.
"""
import os
import re
import sys

VERBS = (
    "Get|Set|Change|Play|Start|Stop|Show|Push|Reset|Enable|Disable|Update|Request|Apply|Save|Load|Restart|Reboot|"
    "Event|Notify|Query|Send|Run|Check|Clear|Read|Write|Delete|Add|Remove|Create|Upload|Download|Trigger|Calibrate|"
    "Test|Unlock|Lock|Enroll|Verify|Identify|Scan|Sync|Report|Dump|Take|Wake|Mute|Switch|Toggle|Refresh|Register|"
    "Adopt|Provision|Upgrade|Ping|Custom|MCU"
)
NAME = re.compile(rb"^(" + VERBS.encode() + rb")[A-Z][A-Za-z0-9]{2,40}$")


def names_in(path):
    data = open(path, "rb").read()
    if data[:2] == b"#!":
        return []
    found = {m.group(0).decode() for m in re.finditer(rb"[ -~]{6,}", data) if NAME.match(m.group(0))}
    return sorted(found)


def main(paths):
    print("# IPC message names found in service binaries. Names only; not proof the service handles them.\n")
    for path in paths:
        if not os.path.isfile(path):
            continue
        names = names_in(path)
        if not names:
            continue
        commands = [n for n in names if not n.startswith("Event")]
        events = [n for n in names if n.startswith("Event")]
        print(f"## {os.path.basename(path)}")
        print("commands: " + (" ".join(commands) or "(none found)"))
        print("events: " + (" ".join(events) or "(none found)"))
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
