<img align="right" src="logo.png">

## The Craftr build system

<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square"></a>
<img src="https://img.shields.io/badge/version-3.0.1--dev-blue.svg?style=flat-square"/>
<a href="https://travis-ci.org/craftr-build/craftr"><img src="https://travis-ci.org/craftr-build/craftr.svg?branch=master"></a>
<a href="https://ci.appveyor.com/project/NiklasRosenstein/craftr/branch/master"><img src="https://ci.appveyor.com/api/projects/status/6v01441cdq0s7mik/branch/master?svg=true"></a>

Craftr is a new software build system with a focus on ease of use, granularity
and extensibility. It is language independent and supports a wide range of
popular programming languages out of the box. Craftr uses [Ninja] to execute
builds.

__Inspiration__

* [Buck](https://buckbuild.com/)
* [CMake](https://cmake.org/)
* [QBS](https://bugreports.qt.io/projects/QBS/summary)

__Install__

Craftr 3 is work in progress and not currently available on PyPI. If you
install `craftr-build` via Pip, you will install Craftr 2 which is vastly
different from this version. To get *this* version, you have to install it
directly from the GitHub repository.

    pip3 install git+https://github.com/craftr-build/craftr.git@master

__Examples__

<table>
  <tr><th>C</th><th>C++</th></tr>
  <tr>
    <td>

```python
project "examples.c"
using "cxx"
target "main":
  cxx.srcs = ['main.c']
```

Run as `craftr -cb main:cxx.run`
</td>
<td>

```python
project "examples.cpp"
using "cxx"
target "main":
  cxx.srcs = ['main.cpp']
```

Run as `craftr -cb main:cxx.run`
</td>
  </tr>
  <tr><th>C#</th><th>Java</th></tr>
  <tr>
    <td>

```python
project "examples.csharp"
using "csharp"
target "main":
  csharp.srcs = glob('src/*.cs')
  csharp.packages = ['Newtonsoft.JSON:10.0.3']
  csharp.bundle = True
```

Run as `craftr -cb main:csharp.runBundle`
</td>
    <td>

```python
project "examples.java"
using "java"
target "main":
  java.srcs = glob('src/**/*.java')
  java.artifacts = [
      'org.tensorflow:tensorflow:1.4.0'
    ]
  java.mainClass = 'Main'
  java.bundleType = 'merge'  # Or 'onejar'
```

Run as `craftr -cb main:java.runBundle`
</td>
  </tr>
  <tr><th>Haskell</th><th>OCaml</th></tr>
  <tr>
    <td>

```python
project "examples.haskell"
using "haskell"
target "main":
  haskell.srcs = ['src/Main.hs']
```

Run as `craftr -cb main:haskell.run`
</td>
    <td>

```python
project "examples.ocaml"
using "ocaml"
target "main":
  ocaml.srcs = ['src/Main.ml']
  # False to produce an OCaml bytecode file
  ocaml.standalone = True
```

Run as `craftr -cb main:ocaml.run`
</td>
  </tr>
  <tr><th>Vala</th><th>Cython</th></tr>
  <tr>
    <td>

```python
project "examples.vala"
using "vala"
target "main":
  vala.srcs = ['src/Main.vala']
```

Run as `craftr -cb main:vala.run`
</td>
    <td>

```python
project "example.cython"
using "cython"
target "main":
  cython.srcs = glob('src/*.pyx')
  cython.main = 'src/Main.pyx'
```

Run as `craftr -cb main:cython.run`
</td>
  </tr>
</table>

---

<p align="center">Copyright &copy; 2015-2018 &nbsp; Niklas Rosenstein</p>
