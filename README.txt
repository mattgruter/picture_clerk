============
PictureClerk
============

PictureClerk is a command-line tool to assist you with your photography
workflow.

Execute PictureClerk like this::

    #!/usr/bin/env bash
    ./picture_clerk/cli.py --help    

This will print some helpful information about how to invoke the program.


Dependencies
============

Core
----
* 2.7 <= python < 3
* python-pyexiv2
* python-paramiko
* python-dulwich
* jhead

UI
--
* qiv

Test
----
* python-mock


Development
===========
Use virtualenv to set up a clean Python installation for development.

On Ubuntu install the following packages
* python-virtualenv
* python-dev

In the virtualenv install the following packages with 'pip install ...':
* paramiko
* pyexiv2 (not availble through pip (yet), symlink from global dist/site-packages instead)
* mock
