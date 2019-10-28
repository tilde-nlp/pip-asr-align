#!/bin/bash

export LC_ALL=lt_LT.utf8
. ./setup.sh

tokenize="/data/Projekti/tools/text/tokenizer.perl -l lt -threads 1 -lines 750000"


echo "--Normalizing texts--"
for txt in text/*
do  
    # remove nbsp
    # shorten surnames G.Berzina -> Berzina
    sed 's/\xc2\xad//g' "$txt" |\
    sed "s/\b\([[:upper:]]\|Dr\)\.\([[:upper:]][[:lower:]]\+\b\)/\2/g" |\
    $tokenize | tr -cd '[[:alnum:] ĄąĖėĘęĮįŲųŪūČčŠšŽž\n]' |\
    sed -r 's/[[:space:]]{2,}/ /g' |\
    sed -r 's/^[[:space:]]+//' | sed 's/[[:space:]]+$//' |\
    $TOOLS/text/tolower_except.py $ABBR_EXCEPTION_LIST_LT |\
    > ref/`basename "$txt"`
#    normalizer is not a part of this package, unfortunately    
#    $TOOLS/text/normalizer.py -r -n -c lt  > ref/`basename "$txt"`
done

