Making a new release
====================

This page describes how to create a new release of the certification suite.

github branching
----------------

If you are creating a release for the first time for a new version of Firefox OS, you should create a new branch in github for it, e.g.,:

    git branch v2.1
    git checkout v2.1
    git push origin v2.1

The master branch should be retained as a development branch; releases should not be made directly from it.

versioning
----------

You should verify that *certsuite/config.json* has the correct two-digit version number this release supports.  This version number is passed to the individual components of the suite as they're run.

The package version in *setup.py* should be bumped with each release.  For a release tracking Firefox OS 2.1, for example, the valid package versions are 2.1.0, 2.1.1, etc.

archive generation
------------------

The contents of the *fxos-certsuite* directory are copied to another directory with a name in the format *fxos-MCTS-2.1.0*, and the hidden *.git* directory is removed.  The *documentation.pdf* file in the root directory is updated using command

    *make latexpdf*

in the *docs* folder.  The resulting PDF file is moved from *_build/latex/FirefoxOSCertificationTestsuite.pdf* to *documentation.pdf* in the root folder, and the *docs/_build* folder is removed.

Finally, the directory is archived using the command:

    zip -r fxos-MCTS-2.1.0.zip fxos-MCTS-2.1.0/

