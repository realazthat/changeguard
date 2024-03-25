# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# The ChangeGuard project requires contributions made to this file be licensed
# under the MIT license or a compatible open source license. See LICENSE.md for
# the license text.
"""Check changes in a directory, before => after. Ignores new files."""

# To run test_list_paths:
#
# ```bash
# python scripts/check-changes.py test_list_paths --directory . --ignorefile \
#   .gitignore --ignoreline .git --ignoreline .trunk
# ```

import argparse
import json
import sys
from pathlib import Path
from typing import List

from rich.console import Console
from typing_extensions import Dict

from . import _build_version
from .changeguard import (_VALID_METHODS, Audit, Hash, TestListPaths,
                          _ConstructIgnorePathSpecs)

_DEFAULT_HASH_CMD = 'xxhsum -H0'


def _AddIgnoreArgs(parser: argparse.ArgumentParser):
  parser.add_argument('--ignorefile',
                      type=argparse.FileType('r'),
                      action='append',
                      default=[],
                      help='File containing additional ignore patterns.'
                      ' Follows gitignore syntax.'
                      ' See <https://github.com/cpburnz/python-pathspec>.'
                      ' Can be used more than once.')
  parser.add_argument('--ignoreline',
                      type=str,
                      action='append',
                      default=[],
                      help='Ignore pattern. Follows gitignore syntax.'
                      ' See <https://github.com/cpburnz/python-pathspec>.'
                      ' Can be used more than once.')


def _AddDirectoryArgs(parser: argparse.ArgumentParser, *, action: str):
  parser.add_argument('--directory',
                      type=Path,
                      required=True,
                      help=f'Directory to {action}.')


def _AddHashingArgs(parser: argparse.ArgumentParser):
  parser.add_argument(
      '--max-workers',
      type=int,
      default=10,
      help='Maximum number of workers to use for hashing. Default is 10.')
  parser.add_argument(
      '--hash-cmd',
      type=str,
      default=_DEFAULT_HASH_CMD,
      help=
      f'Command to hash files with. Default is {json.dumps(_DEFAULT_HASH_CMD)}')


def main():
  console = Console(file=sys.stderr)
  try:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--version', action='version', version=_build_version)

    cmd = parser.add_subparsers(required=True, dest='cmd')
    hash_cmd_parser = cmd.add_parser('hash', help='Hash files in a directory.')
    hash_cmd_parser.add_argument('--method',
                                 choices=_VALID_METHODS,
                                 required=True,
                                 help='Method to use to list files.')
    _AddIgnoreArgs(hash_cmd_parser)
    _AddDirectoryArgs(hash_cmd_parser, action='hash')
    _AddHashingArgs(hash_cmd_parser)
    hash_cmd_parser.add_argument(
        '--tmp-backup-dir',
        type=Path,
        required=False,
        default=None,
        help=
        'Directory to backup files to before hashing. Useful for auditing, to show deltas.'
    )
    hash_cmd_parser.add_argument(
        '--audit-file',
        type=argparse.FileType('w'),
        required=True,
        help='File to output the hashes to, used for auditing.')
    audit_cmd_parser = cmd.add_parser(
        'audit',
        help=
        'Audit files in a directory using an existing audit file produced by `hash` command.'
    )
    _AddDirectoryArgs(audit_cmd_parser, action='audit')
    audit_cmd_parser.add_argument(
        '--audit-file',
        type=argparse.FileType('r'),
        required=True,
        help='File to read hashes from, used for auditing.')
    _AddHashingArgs(audit_cmd_parser)
    audit_cmd_parser.add_argument(
        '--show-delta',
        action='store_true',
        help=
        'Show the delta between the current directory and the --tmp-backup-dir.'
        ' Requires --tmp-backup-dir to be set in the audit file.')
    test_list_paths_cmd_parser = cmd.add_parser(
        'test_list_paths',
        help=
        'Test listing paths using git and initial_iterdir, and check if they match.'
    )
    _AddIgnoreArgs(test_list_paths_cmd_parser)
    _AddDirectoryArgs(test_list_paths_cmd_parser, action='list')

    args = parser.parse_args()

    if args.cmd == 'hash':
      ignore_metas: Dict[str, List[str]] = {}
      ignores = _ConstructIgnorePathSpecs(ignorefiles=list(args.ignorefile),
                                          ignorelines=list(args.ignoreline),
                                          ignore_metas=ignore_metas)
      return Hash(hash_cmd=args.hash_cmd,
                  directory=args.directory,
                  method=args.method,
                  audit_file=args.audit_file,
                  ignores=ignores,
                  ignore_metas=ignore_metas,
                  max_workers=args.max_workers,
                  tmp_backup_dir=args.tmp_backup_dir,
                  console=console)

    elif args.cmd == 'audit':
      return Audit(hash_cmd=args.hash_cmd,
                   directory=args.directory,
                   audit_file=args.audit_file,
                   max_workers=args.max_workers,
                   show_delta=args.show_delta,
                   console=console)
    elif args.cmd == 'test_list_paths':
      return TestListPaths(directory=args.directory,
                           ignorefiles=list(args.ignorefile),
                           ignorelines=list(args.ignoreline),
                           console=console)
    else:
      raise argparse.ArgumentError(argument=None,
                                   message=f'Unknown command {args.cmd},'
                                   ' expected {hash, audit}.')
  except Exception:
    console.print_exception()
    sys.exit(1)


if __name__ == '__main__':
  main()
