#!/bin/bash

export LC_ALL=lv_LV.utf8
. ./setup.sh

echo "--Normalizing texts--"
for txt in text/*
do
    # add spaces between cardinal numbers and words
    # spaces instead of dashes in "named entities"
    # shorten surnames G.Berzina -> Berzina
    # pulksten 14. 00 --> pulksten 14 00
    sed "s/\([0-9]\+\.\)\(\w\)/\1 \2/g" $txt |\
    sed "s/\([[:upper:]]\w*\)-\([[:upper:]]\)/\1 \2/g" |\
    sed "s/\([[:upper:]]\)\.\([[:upper:]]\)/\2/g" |\
    sed "s/\(pulksten [0-9]\+\)\./\1/g" |\
    utils/text/tolower_except.py $ABBR_EXCEPTION_LIST_LV |\
    > ref/`basename $txt`
#    normalizer is not a part of this package unfortunately
#    $TOOLS/text/normalizer.py -r -n -c  > ref/`basename $txt`
done
