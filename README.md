C++ Ninja Build Framework
=========================

Build framework for C++ using g++ and ninja. Run

    $ make
    $ ninja

Every folder below ``source`` will be build by default as library. ``*.cpp``
files under ``source/foo/bar/`` generate ``foo_bar.a``. Files directly under
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
not supported.

