PictureClerk
============

PictureClerk is a command-line tool to assist you with your photography
workflow.

Execute PictureClerk like this:

```bash
./picture_clerk/cli.py --help    
```

This will print some helpful information about how to invoke the program.


Dependencies
------------

You need Python 2.7 to run PictureClerk. Python 3 is not supported yet, mainly due to the fact that pyexiv2 does not yet support it.

Furthermore the tools "qiv" and "jhead" are required by PictureClerk.

A list over necessary Python modules can be found in the file requirements.txt


Development
-----------

Use virtualenv to set up a clean Python installation for development.

On Ubuntu install the following packages
* python-dev
* python-virtualenv
* virtualenvwrapper

Then run the following commands to create the development environment:

```bash
mkvirtualenv -a [PROJECTPATH] -r requirements.txt --python /usr/bin/python2.7 --no-site-packages pic
ln -s /usr/lib/python2.7/dist-packages/{libexiv2python.so,pyexiv2} "$WORKON_HOME"/pic/lib/python2.7/site-packages
```
