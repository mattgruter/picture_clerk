#!/bin/sh

cd test_album
rm -f *.err *.log *.xmp *.thumb.jpg *.sha1
rm -rf .git/
rm -rf .pic.db
rm -rf log/*
rmdir log
cd ..
