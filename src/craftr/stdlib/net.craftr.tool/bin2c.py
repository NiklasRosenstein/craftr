# -*- coding: utf8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2018  Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Convert one or more files into a single C implementation file and optionally
a header file for embedding in a C/C++ application.
"""

import argparse
import collections
import contextlib
import io
import os
import re
import sys


HEADER = '/* Auto-generated by the Craftr build system / bin2c.py */'


class ConcatFile:

  def __init__(self, *files):
    self._files = []
    self._type = None

    queue = list(files)
    while queue:
      f = queue.pop(0)
      if isinstance(f, str):
        assert self._type in (str, None), self._type
        self._type = str
        f = io.StringIO(f)
      elif isinstance(f, bytes):
        assert self._type in (bytes, None), self._type
        self._type = bytes
        f = io.BytesIO(f)
      else:
        if self._type is None:
          queue.insert(0, f)
          queue.insert(0, f.read(1))
          continue
      self._files.append(f)

  def __enter__(self):
    for f in self._files:
      if hasattr(f, '__enter__'):
        f.__enter__()
    return self

  def __exit__(self, *args):
    for f in self._files:
      if hasattr(f, '__enter__'):
        f.__exit__(*args)

  def read(self, n):
    data = self._type()
    while len(data) < n and self._files:
      temp = self._files[0].read(n - len(data))
      if not temp:
        self._files.pop(0)
      data += temp
    return data


@contextlib.contextmanager
def open_cli_file(filename, mode):
  if not filename or filename == '-':
    assert mode == 'w'
    yield sys.stdout
  else:
    with open(filename, mode) as fp:
      yield fp


@contextlib.contextmanager
def write_namespace(fp, namespace):
  if namespace:
    for x in namespace.split('::'):
      fp.write('namespace {} {{\n'.format(x))
    fp.write('\n')
  yield
  if namespace:
    for x in namespace.split('::'):
      fp.write('}} // namespace {}\n'.format(x))


def write_header(fp, files, namespace, static, cpp, cstring=False, cppstring=False):
  fp.write(HEADER + '\n')
  fp.write('#pragma once\n')
  fp.write('#include <{}>\n'.format('cstddef' if cpp else 'stddef.h'))
  if cppstring and cpp:
    fp.write('#include <string>\n')
  fp.write('\n')
  if not cpp:
    fp.write('#ifdef __cplusplus\nextern "C" {\n#endif\n\n')
  with write_namespace(fp, namespace if cpp else None):
    if static:
      write_data(fp, files, namespace=None, static=static, cpp=cpp,
        cstring=cstring, cppstring=cppstring)
    else:
      for s in files.values():
        fp.write('extern unsigned char const {}_start[];\n'.format(s))
        fp.write('extern size_t const {}_size;\n'.format(s))
        if cstring and not cpp:
          fp.write('extern char const* const {}_string;\n'.format(s))
        if cppstring and cpp:
          fp.write('extern std::string const {}_string;\n'.format(s))
        fp.write('\n')
  if not cpp:
    fp.write('#ifdef __cplusplus\n} // extern "C"\n#endif\n\n')


def write_impl(fp, files, namespace, cpp, cstring=False, cppstring=False):
  if cpp and namespace:
    write_header(fp, files, namespace, False, cpp, cstring, cppstring)
    fp.write('\n')
  else:
    # TODO: It's basically the same as in write_header() here.
    fp.write(HEADER + '\n')
    fp.write('#include <{}>\n'.format('cstddef' if cpp else 'stddef.h'))
    if cppstring and cpp:
      fp.write('#include <string>\n')
    fp.write('\n')

  write_data(fp, files, namespace=namespace, static=False,
    cpp=cpp, impl=True, cstring=cstring, cppstring=cppstring)


def write_data(fp, files, namespace, static, cpp, impl, cstring, cppstring):
  static = 'static ' if static else ''
  prefix = '{}::'.format(namespace) if (namespace and cpp) else ''
  for f, s in files.items():
    s = prefix + s
    fp.write('{}unsigned char const {}_start[] = {{\n'.format(static, s))
    with ConcatFile(open(f, 'rb'), b'\0') as src:  # Always add a 0 terminator
        size = 0
        while True:
          data = src.read(16)
          if not data: break
          size += len(data)
          fp.write('\t')
          for c in data:
            fp.write('0x{:02X},'.format(c))
          fp.write('\n')
    fp.write('};\n')
    fp.write('{}size_t const {}_size = {};\n'.format(static, s, size - 1))
    if cstring:
      fp.write('{0}char const* const {1}_string = (char*) {1}_start;\n'.format(static, s))
    if cppstring and cpp and not cstring:
      fp.write('{0}std::string const {1}_string((char*){1}_start, {1}_size);\n'.format(static, s))
    fp.write('\n')


def get_argument_parser(prog=None):
  parser = argparse.ArgumentParser(prog=prog, add_help=False, allow_abbrev=False)
  parser.add_argument('--help', action='help')

  group = parser.add_argument_group('Input')
  group.add_argument(
    'files',
    metavar='FILE[=SYM]',
    nargs='+',
    help='One or more input files. A file may be suffix with the C/C++ '
         'symbol name.')

  group = parser.add_argument_group('Output')
  group.add_argument('--c', metavar='FILE', help='The C output file.')
  group.add_argument('--h', metavar='FILE', help='The C header output file.')
  group.add_argument('--cpp', metavar='FILE', help='The C++ output file.')
  group.add_argument('--hpp', metavar='FILE', help='The C++ header output file.')
  group.add_argument('-n', '--namespace', metavar='NAMESPACE', help='The C++ namespace.')
  group.add_argument('-s', '--static', action='store_true', help='Write to header as static data.')
  group.add_argument('--cstring', action='store_true', help='Write a C-string representation (precedence over --cppstring).')
  group.add_argument('--cppstring', action='store_true', help='Write a C++-string representation.')

  return parser


def main(argv=None, prog=None):
  parser = get_argument_parser(prog)
  args = parser.parse_args(argv)

  files = collections.OrderedDict()
  for f in args.files:
    f, s = f.partition('=')[::2]
    if not s:
      s = re.sub('[^\w\d_]+', '_', os.path.basename(f))
    files[f] = s

  if args.h:
    with open_cli_file(args.h, 'w') as fp:
      write_header(fp, files, args.namespace, args.static, False, args.cstring, args.cppstring)

  if args.c:
    with open_cli_file(args.c, 'w') as fp:
      write_impl(fp, files, args.namespace, False, args.cstring, args.cppstring)

  if args.hpp:
    with open_cli_file(args.hpp, 'w') as fp:
      write_header(fp, files, args.namespace, args.static, True, args.cstring, args.cppstring)

  if args.cpp:
    with open_cli_file(args.cpp, 'w') as fp:
      write_impl(fp, files, args.namespace, True, args.cstring, args.cppstring)


if __name__ == '__main__':
  sys.exit(main())