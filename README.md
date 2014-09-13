C++ Ninja Build Framework
=========================

Simple build framework for C++ using g++ and
[ninja](http://martine.github.io/ninja).

```bash
$ make projects        # Generate build.ninja and Sublime Text project.
$ make build           # Generate build.ninja and call ninja.
$ make doxygen         # Generate Doxygen documentation.
$ make                 # Generate build.ninja, projects and call ninja.
```

Use ``make DEBUG=<target_name> ...`` to generate build.ninja with debug
flags and configure Sublime Text project file to debug given target with
[SublimeGDB](https://github.com/quarnster/SublimeGDB).

Once build.ninja has been generated, ninja can be called directly

```bash
$ ninja                # Build all.
$ ninja <target_name>  # Build specific target.
```

Every folder below ``source`` is built by default as library. ``*.cpp`` files
under ``source/foo/bar/`` generate ``foo_bar.a``. Files directly under
``source/`` generate ``root.a``.

To build an executable add a ``rules.gyp`` to the folder, as e.g.

```JSON
{
  "targets": [
    {
      "target_name": "foobar",
      "dependencies": [ "foo_bar.a", "root.a" ]
    }
  ]
}
```

note that the order of ``dependencies`` matter. Use plain JSON, gyp syntax is
not yet supported.
