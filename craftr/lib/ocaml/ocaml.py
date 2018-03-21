
import craftr
from nr import path

if OS.name == 'nt':
  exe_suffix = '.exe'
else:
  exe_suffix = ''


class OcamlTargetHandler(craftr.TargetHandler):

  def init(self, context):
    props = context.target_properties
    props.add('ocaml.srcs', craftr.StringList)
    props.add('ocaml.standalone', craftr.Bool)
    props.add('ocaml.productName', craftr.String)
    props.add('ocaml.compilerFlags', craftr.StringList)

  def translate_target(self, target):
    src_dir = target.directory
    build_dir = path.join(context.build_directory, target.module.name)
    data = target.get_props('ocaml.', as_object=True)
    data.compilerFlags = target.get_prop_join('ocaml.compilerFlags')

    if not data.productName:
      data.productName = target.name + '-' + target.module.version
    if data.srcs:
      data.srcs = [path.canonical(x, src_dir) for x in data.srcs]
      data.productFilename = path.join(build_dir, data.productName)
      if data.standalone:
        data.productFilename += exe_suffix
      else:
        data.productFilename += '.cma'
      target.outputs.add(data.productFilename, ['exe'])

    if data.srcs:
      # Action to compile an executable.
      command = ['ocamlopt' if data.standalone else 'ocamlc']
      command += ['-o', '$out', '$in']
      action = target.add_action('ocaml.compile', commands=[command])
      build = action.add_buildset()
      build.files.add(data.srcs, ['in'])
      build.files.add(data.productFilename, ['out'])

      # Action to run the executable.
      command = [data.productFilename]
      action = target.add_action('ocaml.run', commands=[command],
        explicit=True, syncio=True, output=False)
      action.add_buildset()


context.register_handler(OcamlTargetHandler())
