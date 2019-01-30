#! /usr/bin/env python3
'''
merge_history.py
Utility for use with multi-shell history management.

Merges multiple individual shell history files into
combined history files including all shell histories
for each shell
'''

import os
import os.path
import sys
import json
from datetime import datetime
import argparse


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


def build_mergefile(mergename, mergetime, shell_stats, dry_run=False):
    special_shellname = mergename.replace("merged", "shell")
    tocname = mergename.replace("merged", "toc")
    tocdata = None
    if dry_run:
        print("Building merge file %s for shell %s" % (mergename, special_shellname))

    try:
        # toc data format:
        # [[filename, timestamp, end_position], ...]
        with open(tocname, "r") as tocfile:
            if dry_run:
                print("   Loading TOC file %s" % tocname)
            rawtoc = tocfile.read()
            tocdata = json.loads(rawtoc)
    except FileNotFoundError as fnf:
        if dry_run:
            print("   TOC file not found" % tocname)
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
            if dry_run:
                print("   Shell history %s unchanged, skipping %s merged bytes" % (
                    shellname, filesize))
            change_seekpos += filesize
            toc_idx += 1
        else:
            if dry_run:
                print("   Will write shell history %s, %s bytes" % (
                    shellname, filesize))
            if change_looking:
                change_looking = False

            change_files.append([shellname, timestamp, filesize])

        updated_toc.append(
            [shellname, timestamp, filesize]
        )

    if dry_run:
        print("Writing TOC file %s" % tocname)
        print("Writing merged file")
        return

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

def main():
    parser = argparse.ArgumentParser(description="Manage multiple shell history files")
    parser.add_argument(
        '--update', '-u', action='store_true',
        help='Update existing history and TOC files (if needed)'
    )
    parser.add_argument(
        '--init', '-i', action='store_true',
        help='Ensure the existence of merge and TOC files'
    )
    parser.add_argument(
        '--histdir', '-d', default=os.environ.get("SHELL_HISTDIR"),
        help='Path to store per-shell and merged history files'
    )
    parser.add_argument(
        '--shellfile', '-s', default=os.environ.get("SHELL_HISTFILE"),
        help='History file for commands entered in this shell'
    )
    parser.add_argument(
        '--prune', '-p', action='store_true',
        help='Delete merge and TOC files'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Do nothing, print what actions would be taken'
    )

    args = vars(parser.parse_args())

    histdir = args.get('histdir')
    shellhist = args.get('shellfile')
    dry_run = args.get('dry_run')

    if dry_run:
        print("Got --dry-run, will not modify files")

    if not (
        os.path.isdir(histdir)
        and os.access(histdir, os.W_OK)
        and os.access(histdir, os.R_OK)
    ):
        print("multihist: history directory '%s' is not a read/writable directory" % histdir)
        sys.exit(-1)

    shell_stats, merged_stats = stat_shell_histories(histdir)
    shell_stats.sort(key=lambda e: e[1])
    merged_stats.sort(key=lambda e: e[1])
    newest_mergetime = merged_stats[-1][1] if merged_stats else 0
    newest_shelltime = shell_stats[-1][1] if shell_stats else 0

    mergefiles = [m[0] for m in merged_stats]
    do_rebuild = False

    if args.get('prune'):
        for mergefile in mergefiles:
            if os.is_file(mergefile):
                if dry_run:
                    print("Remove mergefile %s" % mergefile)
                else:
                    os.remove(mergefile)
            tocfilename = mergefile.replace('merged-', 'toc-')
            if os.is_file(tocfilename):
                if dry_run:
                    print("Remove TOC file %s" % tocfilename)
                else:
                    os.remove(tocfilename)

    mergefilename = shellhist.replace('shell-', 'merged-')

    if mergefilename not in mergefiles:
        do_rebuild = True
        mergefiles.append(mergefilename)

    if args.get('init'):
        if dry_run:
            print("Initializing, will update merge files...")
        do_rebuild = True

    elif args.get('update'):
        if newest_shelltime > newest_mergetime:
            if dry_run:
                print("Will update, mergefile timestamp %s older than %s" % (
                    newest_shelltime, newest_mergetime))
            do_rebuild = True

    if do_rebuild:
        for mergefile in mergefiles:
            build_mergefile(mergefile, newest_mergetime, shell_stats, dry_run)


if __name__ == "__main__":
    main()
