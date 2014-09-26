C++ Ninja Build Framework
=========================

Simple build framework for C++ using g++ and
[ninja](http://martine.github.io/ninja).

```bash
$ make configure       # Generate build.ninja (and update Makefile).
$ make sublime         # Generate Sublime Text project.
$ make doxygen         # Generate Doxygen documentation.
$ ninja                # Build default configuration.
```

Targets in the makefile call ``tools/configure.py``. Call ninja directly to
avoid parsing source directory tree everytime, use the makefile only when
targets have changed. See ``tools/configure.py --help`` for more options.

Default settings
----------------

See ``tools/settings.json``. By default the following targets are available

```bash
$ ninja all
$ ninja debug
$ ninja release  # (default)
$ ninja doxygen
$ ninja <target_name>_debug
$ ninja <target_name>_release
```

Every folder below ``source`` is built by default as static library (dynamic
libraries are not supported). ``*.cpp`` files under ``source/foo/bar/`` generate
``foo_bar.a``. Files directly under ``source/`` generate ``root.a``.

To specify different target rules add a ``rules.gyp`` to the folder, e.g. to
build an executable add

```JSON
{
  "targets": [
    {
      "target_name": "foobar",
      "type": "executable",
      "dependencies": [ "foo_bar.a", "root.a" ]
    }
  ]
}
```

note that the order of ``dependencies`` matter. Use plain JSON, gyp syntax is
not yet supported.
