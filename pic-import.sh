#!/bin/bash

set -e
#set -x

src="$1"
dest="$2"

function find_album_date() {
    image=$( ls "$1"/*.{NEF,JPG} | sort -n | head -1 )

    IFS=': '
    set $(exiv2 -g Exif.Image.DateTime -Pv $image)
    unset IFS
    date=$1$2$3

    echo $date
}

function create_checksums() {
    dir="$1"

    cfv -q -C -r -t sha1 -f sha1sums.txt "$dir"
}

function copy_images() {
    src="$1"
    dest="$2"

    cp -r "$src" "$dest"
}

function verify_checksums() {
    dir="$1"

    cfv -p "$dir" -f sha1sums.txt
}

function import_into_pictureclerk() {
    dir="$1"

    cd "$1"
    pic init
    pic add *.{NEF,JPG}
    cat .pic/sha1/*.sha1 > sha1sums.pic.txt
    diff sha1sums.txt sha1sums.pic.txt
}

function cleanup() {
    dir="$1"

    rm sha1sums.txt sha1sums.pic.txt
}

date=$( find_album_date "$src" )
create_checksums "$src"
copy_images "$src" "$dest"/$date
verify_checksums "$dest"
import_into_pictureclerk "$dest"
cleanup "$dest"
echo
echo "Importing $src to $dest/$date done."

