C++ Ninja Build Framework
=========================

Simple build framework for C++ using g++ and
[ninja](http://martine.github.io/ninja).

```bash
$ make projects        # Generate ninja.build and sublime text project.
$ make build           # Generate ninja.build and call ninja.
$ make                 # Generate ninja.build, projects and call ninja.
```

once ``ninja.build`` has been generated, ninja can be called directly

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

