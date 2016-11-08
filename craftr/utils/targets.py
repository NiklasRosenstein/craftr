# The Craftr build system
# Copyright (C) 2016  Niklas Rosenstein
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from craftr.core import build
from craftr.core.logging import logger
from craftr.core.session import session
from craftr.utils import argspec
from nr.py.bytecode import get_assigned_name

import collections
import sys


def get_full_name(target_name, module=None):
  """
  Given a *target_name*, this function generates the fully qualified name of
  that target that includes the *module* name and version. If *module* is
  omitted, the currently executed module is used.
  """

  if module is None:
    if not session:
      raise RuntimeError('no session context')
    module = session.module
    if not module:
      raise RuntimeError('no current module')

  return '{}.{}'.format(module.ident, target_name)


def gtn(target_name=None, name_hint=NotImplemented):
  """
  This function is mandatory in combination with the :class:`TargetBuilder`
  class to ensure that the correct target name can be deduced. If the
  *target_name* parmaeter is specified, it is returned right away. Otherwise,
  if it is :const:`None`, :func:`get_assigned_name` will be used to retrieve
  the variable name of the expression of 2 frames above this call.

  To visualize the behaviour, imagine you are using a target generator function
  like this:

  .. code:: python

      objects = cxx_compile(
        srcs = glob(['src/*.cpp'])
      )

  The ``cxx_compile()`` function would use the :class:`TargetBuilder`
  similar to what is shown below.

  .. code:: python

      builder = TargetBuilder(inputs, frameworks, kwargs, name = gtn(name))

  And the :func:`gtn` function will use the frame that ``cxx_compile()`` was
  called from to retrieve the name of the variable "objects". In the case that
  an explicit target name is specified, it will gracefully return that name
  instead of figuring the name of the assigned variable.

  If *name_hint* is :const:`None` and no assigned name could be determined,
  no exception will be raised but also no alternative target name will
  be generated and :const:`None` will be returned. This is useful for wrapping
  existing target generator functions.
  """

  if not session:
    raise RuntimeError('no session context')
  module = session.module
  if not module:
    raise RuntimeError('no current module')

  if target_name is None:
    try:
      target_name = get_assigned_name(sys._getframe(2))
    except ValueError:
      if name_hint is NotImplemented:
        raise

  if target_name is None:
    if name_hint is None:
      return None

    index = 0
    while True:
      target_name = '{}_{:0>4}'.format(name_hint, index)
      full_name = get_full_name(target_name, module)
      if full_name not in session.graph.targets:
        break
      index += 1

  return get_full_name(target_name, module)


class TargetBuilder(object):
  """
  This is a helper class for target generators that does a lot of convenience
  handling such as creating a :class:`OptionMerge` from the build options
  specified with the *options* argument or from the input
  :class:`Targets<build.Target>`.

  :param name: The name of the target. Derive this target name by using
    the :func:`gtn` function.
  :param option_kwargs: A dictionary of additional call-level options
    that have been passed to the target generator function. These will
    take top priority in the :class:`OptionMerge`.
  :param inputs: A list of input files or :class:`build.Target` objects
    from which the outputs will be used as input files and the build
    options will be included in the :class:`OptionMerge`.
  :param options: A list of build options that will be included in the
    :class:`OptionMerge`.
  :param outputs: A list of output filenames.
  :param implicit_deps: A list of filenames added as implicit dependencies.
  :param order_only_deps: A list of filenames added as order only dependencies.
  """

  def __init__(self, name, option_kwargs=None, options=(), inputs=None,
      outputs=None, implicit_deps=None, order_only_deps=None):
    argspec.validate('name', name, {'type': str})
    argspec.validate('option_kwargs', option_kwargs, {'type': [None, dict]})
    argspec.validate('options', options,
        {'type': [list, tuple], 'items': {'type': dict}})
    argspec.validate('inputs', inputs,
        {'type': [None, list, tuple], 'items': {'type': [str, build.Target]}})
    argspec.validate('outputs', outputs,
        {'type': [None, list, tuple], 'items': {'type': str}})
    argspec.validate('implicit_deps', implicit_deps,
        {'type': [None, list, tuple], 'items': {'type': str}})
    argspec.validate('order_only_deps', order_only_deps,
        {'type': [None, list, tuple], 'items': {'type': str}})

    options = list(options)
    if inputs is not None:
      self.inputs = []
      for input_ in (inputs or ()):
        if isinstance(input_, build.Target):
          options += input_.options
          self.inputs += input_.outputs
        else:
          self.inputs.append(input_)
    else:
      self.inputs = None

    self.name = name
    self.option_kwargs = option_kwargs or {}
    self.options = options
    self.options_merge = OptionMerge(option_kwargs, *options)
    self.outputs = outputs
    self.implicit_deps = implicit_deps
    self.order_only_deps = order_only_deps
    self.metadata = {}
    self.used_option_keys = set()

  def get(self, key, default=None):
    self.used_option_keys.add(key)
    return self.options_merge.get(key, default)

  def get_list(self, key):
    self.used_option_keys.add(key)
    return self.options_merge.get_list(key)

  def build(self, commands, inputs=None, outputs=None, implicit_deps=None,
      order_only_deps=None, metadata=None, **kwargs):
    """
    Create a :class:`build.Target` from the information in the builder,
    add it to the build graph and return it.
    """

    unused_keys = set(self.option_kwargs.keys()) - self.used_option_keys
    if unused_keys:
      logger.warn('TargetBuilder: "{}" unhandled option keys'.format(self.name))
      logger.indent()
      for key in unused_keys:
        logger.warn('[-] {}={!r}'.format(key, self.option_kwargs[key]))
      logger.dedent()

    # TODO: We could make this a bit shorter..
    if inputs is None:
      inputs = self.inputs or ()
    elif self.inputs is not None:
      raise RuntimeError('inputs specified in constructor and build()')
    if outputs is None:
      outputs = self.outputs or ()
    elif self.outputs is not None:
      raise RuntimeError('outputs specified in constructor and build()')
    if implicit_deps is None:
      implicit_deps = self.implicit_deps or ()
    elif self.implicit_deps is not None:
      raise RuntimeError('implicit_deps specified in constructor and build()')
    if order_only_deps is None:
      order_only_deps = self.order_only_deps or ()
    elif self.order_only_deps is not None:
      raise RuntimeError('order_only_deps specified in constructor and build()')
    if metadata is None:
      metadata = self.metadata
    elif self.metadata:
      raise RuntimeError('metadata specified in constructor and build()')

    target = build.Target(self.name, commands, inputs, outputs, implicit_deps,
        order_only_deps, metadata=metadata, options=self.options, **kwargs)
    session.graph.add_target(target)
    return target


class OptionMerge(object):
  """
  This class represents a merge of dictionaries virtually. Keys in the first
  dictionaries passed to the constructor take precedence over the last.
  """

  def __init__(self, *options):
    self.options = options

  def __getitem__(self, key):
    for options in self.options:
      try:
        return options[key]
      except KeyError:
        pass  # intentional
    raise KeyError(key)

  def get(self, key, default=None):
    try:
      return self[key]
    except KeyError:
      return default

  def get_list(self, key):
    """
    This function returns a concatenation of all list values saved under the
    specified *key* in all option dictionaries in this OptionMerge object.
    It gives an error if one option dictionary contains a non-sequence for
    *key*.
    """

    result = []
    for option in self.options:
      value = option.get(key)
      if value is None:
        continue
      if not isinstance(value, collections.Sequence):
        raise ValueError('found "{}" for key "{}" which is a non-sequence'
            .format(tpye(value).__name__, key))
      result += value
    return result
