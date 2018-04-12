## examples/c-opencl

This example uses OpenCL and OpenGL interop to render the Mandelbrot set.
It shows usage of the following technologies and Craftr build features:

* OpenGL/OpenCL/GLEW/GLFW
* Embedding kernel and shader programs using `cxx.embedFiles`

<table><tr><td>

![](https://i.imgur.com/zlbO7hP.png)
</td><td>

![](https://i.imgur.com/ImzYmAQ.png)
</td></tr></table>

### Build & Run

On Windows, you may have to enable the `craftr/libs/glfw:fromSource` option
and specify your OpenCL vendor, eg. `craftr/libs/opencl:vendor=intel`.

    $ craftr -cf examples/c-opencl -b main:cxx.run

###  To do

* Ubuntu with Intel HD drivers: Getting `error: OpenGL=>OpenCL image could not be created: CL_MEM_OBJECT_ALLOCATION_FAILURE`.
  The `clCreateFromGLTexture2D()` function is not supposed to return this error per the specification.
  Already checked questions for solutions:

    * [AMD Forum: clCreateFromGLTexture2D + GL textures without mipmaps](https://community.amd.com/thread/136580):
      `glGenerateMipmaps(GL_TEXTURE_2D)` did not help.
 