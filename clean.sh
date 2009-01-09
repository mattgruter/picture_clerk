#!/bin/sh

cd test
rm -f *.err *.log *.xmp *.thumb.jpg
rm -rf .git/
cd ..

cd log
rm -f *.err *.log
cd ..
