#! /usr/bin/env python3
'''
merge_history.py
Utility for use with multi-shell history management.

Merges multiple individual shell history files into
combined history files including all shell histories
for each shell
'''

import os
import sys
import json
from datetime import datetime


def stat_shell_histories(histdir):
    shell_stats = []
    merged_stats = []
    for fname in os.listdir(histdir):
        fullpath = os.path.join(histdir, fname)
        filestats = os.stat(fullpath)
        if fname.startswith("shell-"):
            shell_stats.append((fullpath, filestats.st_mtime, filestats.st_size))
        elif fname.startswith("merged-"):
            merged_stats.append((fullpath, filestats.st_mtime, filestats.st_size))
    return shell_stats, merged_stats


def build_mergefile(mergename, mergetime, shell_stats):

    special_shellname = mergename.replace("merged", "shell")
    tocname = mergename.replace("merged", "toc")
    tocdata = None
    try:
        # toc data format:
        # [[filename, timestamp, end_position], ...]
        with open(tocname, "r") as tocfile:
            rawtoc = tocfile.read()
            tocdata = json.loads(rawtoc)
    except FileNotFoundError as fnf:
        tocdata = []
        pass

    updated_toc = []
    toc_idx = 0
    change_looking = True
    change_seekpos = 0
    change_files = []

    for shellname, timestamp, filesize in shell_stats:
        if (toc_idx < len(tocdata)
            and change_looking
            and tocdata[toc_idx][0] == shellname
            and tocdata[toc_idx][1] == timestamp
            and tocdata[toc_idx][2] == filesize
        ):
            change_seekpos += filesize
            toc_idx += 1
        else:
            if change_looking:
                change_looking = False
            change_files.append([shellname, timestamp, filesize])

        updated_toc.append(
            [shellname, timestamp, filesize]
        )

    if change_files:
        special_content = None
        with open(tocname, "w") as tocfile:
            tocfile.write(json.dumps(updated_toc))

        with open(special_shellname, "r") as special_file:
            special_content = special_file.read()

        with open(mergename, "r+") as mergefile:
            mergefile.seek(change_seekpos)
            for shellname, timestamp, filesize in change_files:
                with open(shellname, "r") as infile:
                    contents = infile.read()
                    mergefile.write(contents)
            if special_content:
                mergefile.write(special_content)


if __name__ == "__main__":
    start_time = datetime.utcnow()

    histdir = os.environ.get("SHELL_HISTDIR")
    shell_stats, merged_stats = stat_shell_histories(histdir)
    shell_stats.sort(key=lambda e: e[1])
    merged_stats.sort(key=lambda e: e[1])
    newest_mergetime = merged_stats[-1][1] if merged_stats else 0
    newest_shelltime = shell_stats[-1][1] if shell_stats else 0

    if newest_shelltime > newest_mergetime or "-i" in sys.argv:
        for mergefile, _, _ in merged_stats:
            build_mergefile(mergefile, newest_mergetime, shell_stats)

    elapsed = (datetime.utcnow() - start_time).total_seconds()
