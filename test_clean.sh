#!/bin/sh

cd test_album
rm -f *.err *.log *.xmp *.thumb.jpg *.sha1
rm -rf .git/
cd ..

cd log
rm -f *.err *.log
cd ..
