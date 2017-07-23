configure.pyz
=============

Simple C++ build system for gcc and clang compilers.

Meant to quickly set up and build a C++ project for testing or prototyping.

Features

  * Fast build with ninja
  * Makefile
  * Doxygen documentation
  * Sublime Text project files
  * CodeBlocks project files (experimental)
  * Embedder (experimental)

Creating a project from scratch
-------------------------------

configure.pyz comes with a handy command to initialize a folder with a template
"Hello World" project

    $ mkdir new_project && cd new_project
    $ configure.pyz --hello-world
    $ make && ./bin/hello-world
    Hello World!

It generates the minimal default configuration to build a project with
configure.pyz

  * A "source" folder with a C++ "Hello World".
  * A sample `targets.json` for the given code.
  * A `configure.yaml` with a default build configuration for the project.
  * A build.ninja and a Makefile to build the project.

Minimal example (existing project with dependencies)
----------------------------------------------------

Say you have a project structured as

    your_project/
      source/
        your_static_lib/
          some_files.cpp
          ...
        your_executable/
          main.cpp

where "your_executable" depends on "your_static_lib", and perhaps needs to be
linked against boost system.

The next step is to add some `targets.json` to the folders containing the main
function of an  executable. In this example, it is enough to add one to
"your_executable" folder. A typical `targets.json` would look like

```json
{
	"targets": [
		{
			"target_name": "your_application_name",
			"type": "executable",
			"dependencies": ["your_static_lib.a", "-lboost_system"]
		}
	]
}
```

Note we added "your_static_lib.a" as a dependency. By default, any folder
containing C++ source files it is recognized as static library, and
configure.pyz will generate the targets for compiling as such.

Run configure.pyz

    $ configure.pyz -g --makefile

This generates a `configure.yaml` file containing a defaulted build
configuration, a build.ninja file, and a convenience Makefile with common rules.

If your code is stored under a folder called "source" directly under your root
project, the configuration is most probably done. If not, tweak the generated
`configure.yaml` for your needs.

Once the configuration is done, you can use the Makefile to build the project
and generate other useful resources

    $ make            # build release configuration.
    $ make debug      # build debug configuration.
    $ make doxygen    # build Doxygen documentation.
    $ make sublime    # create a Sublime Text project file.
