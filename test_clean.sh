#!/bin/sh

cd test_album
rm -f *.err *.log *.xmp *.thumb.jpg *.sha1
rm -rf .git/
rm -rf .pic.db
cd ..

cd log
rm -f *.err *.log
cd ..
