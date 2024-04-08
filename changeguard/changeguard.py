# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# The ChangeGuard project requires contributions made to this file be licensed
# under the MIT license or a compatible open source license. See LICENSE.md for
# the license text.

import json
import shlex
import shutil
import subprocess
import sys
import textwrap
import traceback
from concurrent.futures import (FIRST_COMPLETED, Future, ThreadPoolExecutor,
                                wait)
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Set, TextIO

import pathspec
import yaml
from rich.console import Console
from typing_extensions import Literal

_VALID_METHODS = ('initial_iterdir', 'git', 'auto')
_MethodLiteral = Literal['initial_iterdir', 'git', 'auto']


def _Ignore(*, rel_path: Path, ignores: List[pathspec.PathSpec]) -> bool:
  return any(ignore.match_file(str(rel_path)) for ignore in ignores)


def _Execute(*,
             cmd: List[str],
             cwd: Path,
             expected_error_status: int = 0) -> str:
  try:
    output = subprocess.check_output(cmd, cwd=str(cwd), stderr=subprocess.PIPE)
    return output.decode('utf-8')
  except subprocess.CalledProcessError as e:
    if e.returncode == expected_error_status:
      return e.output.decode('utf-8')
    msg = f'Failed to run {json.dumps(cmd[0])}'
    msg += f'\n  Error: {json.dumps(str(e))}'
    msg += f'\n  Command: {json.dumps(shlex.join(cmd))}'
    if e.stderr:
      msg += f'\n  stderr:\n{textwrap.indent(e.stderr.decode("utf-8"), "    ")}'
    if e.stdout:
      msg += f'\n  stdout:\n{textwrap.indent(e.stdout.decode("utf-8"), "    ")}'
    raise Exception(msg) from e


class _PathList(NamedTuple):
  paths: List[Path]
  ignored: List[Path]


def _GetPathsViaIterDir(*, directory: Path,
                        ignores: List[pathspec.PathSpec]) -> _PathList:
  paths: List[Path] = []
  ignored: List[Path] = []
  tovisit = [directory]
  while tovisit:
    tovisit_path = tovisit.pop()
    for child in tovisit_path.iterdir():
      rel_child = child.relative_to(directory)
      if _Ignore(rel_path=rel_child, ignores=ignores):
        ignored.append(child)
        continue
      if child.is_dir():
        tovisit.append(child)
      else:
        paths.append(child)
  paths = [path.relative_to(directory) for path in paths]
  ignored = [path.relative_to(directory) for path in ignored]
  return _PathList(paths=paths, ignored=ignored)


def _GetPathsViaGit(*, directory: Path,
                    ignores: List[pathspec.PathSpec]) -> _PathList:
  cmd = ['git', 'ls-files']
  output: str = _Execute(cmd=cmd, cwd=directory)
  paths: List[Path] = []
  ignored: List[Path] = []
  for line in output.splitlines():
    line = line.strip()
    if len(line) == 0:
      continue
    rel_path = Path(line)
    if not rel_path.exists():
      raise Exception(
          f'git ls-files gave a file that does not exist, line={line}, path.exists(): {rel_path.exists()}'
      )
    if _Ignore(rel_path=rel_path, ignores=ignores):
      ignored.append(rel_path)
      continue
    paths.append(rel_path)
  return _PathList(paths=paths, ignored=ignored)


def _GetPaths(*, directory: Path, method: _MethodLiteral,
              ignores: List[pathspec.PathSpec]) -> _PathList:
  if method == 'initial_iterdir':
    return _GetPathsViaIterDir(directory=directory, ignores=ignores)
  elif method == 'git':
    return _GetPathsViaGit(directory=directory, ignores=ignores)
  elif method == 'auto':
    git_dir = directory / '.git'
    if git_dir.exists():
      return _GetPathsViaGit(directory=directory, ignores=ignores)
    else:
      return _GetPathsViaIterDir(directory=directory, ignores=ignores)
  else:
    raise Exception(
        f'Invalid method, method={method}, valid methods={_VALID_METHODS}')


def _HashPath(*, hash_cmd: str, directory: Path, path: Path) -> str:
  cmd = shlex.split(hash_cmd) + [str(path)]
  output = _Execute(cmd=cmd, cwd=directory)
  parts = output.split()
  if len(parts) != 2:
    raise Exception(
        f'Expected 2 parts in hash output, got {len(parts)}: {json.dumps(output)}'
    )
  hash_str = parts[0]
  return hash_str.strip()


def _HashPaths(*, hash_cmd: str, directory: Path, paths: List[Path],
               max_workers: int) -> List[Future]:
  futures: Set[Future] = set()
  path2fut: Dict[Path, Future] = {}
  with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for path in paths:
      fut = executor.submit(_HashPath,
                            hash_cmd=hash_cmd,
                            directory=directory,
                            path=path)
      path2fut[path] = fut
      futures.add(fut)
      if len(futures) >= max_workers:
        done, futures = wait(futures, return_when=FIRST_COMPLETED)

  return [path2fut[path] for path in paths]


class _Failure(NamedTuple):
  message: Optional[str]
  path: Optional[Path]
  exception: Optional[Exception]


def _CheckFailures(*, failures: List[_Failure], directory: Path,
                   tmp_backup_dir: Optional[Path], console: Console):
  if len(failures) == 0:
    return

  console.print('Failures:', len(failures), style='bold red')
  for failure in failures:
    console.print('Failure:', style='bold red')
    if failure.message:
      console.print(textwrap.indent(failure.message, '  '), style='bold red')
    if failure.path:
      console.print('  at:', failure.path, style='bold red')
    if failure.exception:
      console.print(
          f'  Exception ({type(failure.exception).__name__}):\n{textwrap.indent(str(failure.exception), "    ")}',
          style='bold red')
      __traceback__ = failure.exception.__traceback__
      if __traceback__ is not None:
        console.print('  Exception trace:', style='bold red')
        for (frame, _) in traceback.walk_tb(__traceback__):
          console.print(f'    {frame.f_code.co_filename}:{frame.f_lineno}',
                        style='bold red')
    # console.print(Traceback.from_exception(type(failure.exception), exc_value=failure.exception, traceback=failure.exception.__traceback__))

    if tmp_backup_dir is not None and failure.path is not None:
      # Show delta
      diff = _Execute(cmd=[
          'git', 'diff', '--no-index', '--exit-code',
          str(tmp_backup_dir / failure.path),
          str(directory / failure.path)
      ],
                      expected_error_status=1,
                      cwd=Path.cwd())
      diff = textwrap.indent(diff, '    ')
      console.print('  diff:', style='bold red')
      console.print(diff, style='bold red')

  console.print(f'{"-"*80}', style='bold red')
  console.print('Failures:', len(failures), style='bold red')
  console.print('Exiting due to failures', style='bold red')
  sys.exit(1)


def _ConstructIgnorePathSpecs(
    *, ignorefiles: List[TextIO], ignorelines: List[str],
    ignore_metas: Dict[str, List[str]]) -> List[pathspec.PathSpec]:

  ignores = []
  ignorefile: TextIO
  for ignorefile in ignorefiles:
    ignorefile_contents = ignorefile.read()
    ignorefile_lines: List[str] = ignorefile_contents.splitlines()
    ignore_metas[ignorefile.name] = ignorefile_lines
    ignores.append(
        pathspec.PathSpec.from_lines('gitwildmatch', ignorefile_lines))
  ignore_metas['~ignorelines'] = ignorelines
  ignores.append(pathspec.PathSpec.from_lines('gitwildmatch', ignorelines))
  return ignores


def Hash(*, hash_cmd: str, directory: Path, method: _MethodLiteral,
         audit_file: TextIO, ignores: List[pathspec.PathSpec],
         ignore_metas: Dict[str, List[str]], max_workers: int,
         tmp_backup_dir: Optional[Path], console: Console):
  failures: List[_Failure] = []

  paths: _PathList = _GetPaths(directory=directory,
                               method=method,
                               ignores=ignores)
  hash_futures: List[Future] = _HashPaths(hash_cmd=hash_cmd,
                                          directory=directory,
                                          paths=paths.paths,
                                          max_workers=max_workers)

  audit_dict: Dict[str, Any] = {
      'files': {},
      'tmp_backup_dir':
      str(tmp_backup_dir) if tmp_backup_dir is not None else None,
      '_meta_unused': {
          'directory': str(directory),
          'method': method,
          'hash_cmd': hash_cmd,
          'ignored': list(map(str, paths.ignored)),
          'max_workers': max_workers,
          'ignore_metas': ignore_metas,
      }
  }

  path: Path
  hash_fut: Future
  for path, hash_fut in zip(paths.paths, hash_futures):
    try:
      audit_dict['files'][str(path)] = hash_fut.result()
    except Exception as e:
      failures.append(
          _Failure(
              message=f'Failed to hash file: ({type(e).__name__}) {str(e)}',
              path=path,
              exception=e))
  _CheckFailures(failures=failures,
                 directory=directory,
                 tmp_backup_dir=None,
                 console=console)

  if tmp_backup_dir is not None:
    for path in paths.paths:
      # Copy path to tmp_backup_dir
      dst_path = tmp_backup_dir / path
      dst_path.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy(directory / path, dst_path)
      dst_path.chmod(0o777)

  yaml.safe_dump(audit_dict, audit_file)
  console.print('Hashing complete', style='bold green')


def Audit(*, hash_cmd: str, directory: Path, audit_file: TextIO,
          max_workers: int, show_delta: bool, console: Console):
  failures: List[_Failure] = []
  audit_dict: Dict[str, Any] = yaml.safe_load(audit_file)

  tmp_backup_dir: Optional[Path] = None
  if show_delta:
    if audit_dict.get('tmp_backup_dir', None) is None:
      console.print('Error: show_delta is True, but tmp_backup_dir is None',
                    style='bold red')
      sys.exit(1)
      return
    tmp_backup_dir = Path(audit_dict['tmp_backup_dir'])

  paths: List[Path] = []
  expected_hashes: List[str] = []
  for path_str, expected_hash in audit_dict['files'].items():
    path = Path(path_str)
    if not path.exists():
      failures.append(
          _Failure(message='File does not exist', path=path, exception=None))
      continue
    paths.append(path)
    expected_hashes.append(expected_hash)

  checked_hash_futures: List[Future] = _HashPaths(hash_cmd=hash_cmd,
                                                  directory=directory,
                                                  paths=paths,
                                                  max_workers=max_workers)
  for path, expected_hash, hash_fut in zip(paths, expected_hashes,
                                           checked_hash_futures):
    try:
      actual_hash = hash_fut.result()
      if expected_hash != actual_hash:
        failures.append(
            _Failure(
                message=
                f'Hash mismatch: expected_hash={json.dumps(expected_hash)} actual={json.dumps(actual_hash)}',
                path=path,
                exception=None))
    except Exception as e:
      failures.append(
          _Failure(
              message=f'Failed to hash file: ({type(e).__name__}) {str(e)}',
              path=path,
              exception=e))

  _CheckFailures(failures=failures,
                 directory=directory,
                 tmp_backup_dir=tmp_backup_dir,
                 console=console)
  console.print('Audit passed', style='bold green')
  sys.exit(0)


def TestListPaths(*, directory: Path, ignorefiles: List[TextIO],
                  ignorelines: List[str], console: Console):

  git_dir = directory / '.git'
  if not git_dir.exists():
    console.print(
        'Error: No .git directory found. Test only makes sense inside a git repository.',
        style='bold red')
    sys.exit(1)
    return

  ignores = _ConstructIgnorePathSpecs(ignorefiles=ignorefiles,
                                      ignorelines=ignorelines,
                                      ignore_metas={})
  initial_iterdir_paths = _GetPathsViaIterDir(directory=directory,
                                              ignores=ignores)
  git_paths = _GetPathsViaGit(directory=directory, ignores=ignores)
  delta = set(initial_iterdir_paths.paths) ^ set(git_paths.paths)
  if len(delta) > 0:
    console.print('Error: initial_iterdir_paths and git_paths do not match.',
                  style='bold red')
    dump_dict = {}
    dump_dict['initial_iterdir_paths'] = sorted(
        map(str, initial_iterdir_paths.paths))
    dump_dict['git_paths'] = sorted(map(str, git_paths.paths))
    dump_dict['delta'] = sorted(map(str, (delta)))
    console.print(yaml.safe_dump(dump_dict))
    console.print('Error: initial_iterdir_paths and git_paths do not match.',
                  style='bold red')
    sys.exit(1)
  else:
    console.print('initial_iterdir_paths and git_paths match.',
                  style='bold green')
    sys.exit(0)
