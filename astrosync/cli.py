#!/usr/bin/env python3

import datetime
import argparse
import os
import logging

from astrosync import Syncer

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="astrosync", prog="astrosync")
    parser.add_argument(
        "--src",
        default=os.path.join(os.getenv("HOME"), "Dropbox", "Apps/Postbox"),
        type=str,
        help="The Postbox dir to sync from",
    )

    parser.add_argument(
        "--dst",
        default=os.path.join(os.getenv("HOME"), "Dropbox", "writing",
            str(datetime.date.today().year),
        ),
        type=str,
        help="The writing dir to sync to",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not actually copy files, just report what would be copied",
    )

    args = parser.parse_args()
    syncer = Syncer(args.src, args.dst, args.dry_run)
    syncer.sync()

if __name__ == "__main__":
    main()
