#!/bin/bash

# # Copyright 2014 Tilde
# Apache 2.0

source ./path.sh

srcdir=data/local
lang=data/lang
test=

. utils/parse_options.sh

lm=$1

if [ $# -gt 1 ]; then
  lang=$2
fi

if [ -z "$test" ]; then
  test=$lang
fi


tmpdir=data/local/lm_tmp
lexicon=data/local/dict/lexicon.txt
if [ $# == 3 ]; then
  lexicon=$3
fi
mkdir -p $tmpdir


echo "--- Preparing the grammar transducer (G.fst) for testing ..."

mkdir -p $test
for f in phones.txt words.txt phones.txt L.fst L_disambig.fst phones/; do
    cp -r $lang/$f $test
done
cat $lm | \
   utils/find_arpa_oovs.pl $test/words.txt > $tmpdir/oovs.txt

cat $lm | \
  grep -v '<s> <s>' | \
  grep -v '</s> <s>' | \
  grep -v '</s> </s>' | \
  arpa2fst - | fstprint | \
  utils/remove_oovs.pl $tmpdir/oovs.txt | \
  utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$test/words.txt \
    --osymbols=$test/words.txt  --keep_isymbols=false --keep_osymbols=false | \
  fstrmepsilon | fstarcsort --sort_type=ilabel > $test/G.fst
fstisstochastic $test/G.fst

# Everything below is only for diagnostic.
# Checking that G has no cycles with empty words on them (e.g. <s>, </s>);
# this might cause determinization failure of CLG.
# #0 is treated as an empty word.
mkdir -p $tmpdir/g
awk '{if(NF==1){ printf("0 0 %s %s\n", $1,$1); }} END{print "0 0 #0 #0"; print "0";}' \
  < "$lexicon"  >$tmpdir/g/select_empty.fst.txt
fstcompile --isymbols=$test/words.txt --osymbols=$test/words.txt \
  $tmpdir/g/select_empty.fst.txt | \
fstarcsort --sort_type=olabel | fstcompose - $test/G.fst > $tmpdir/g/empty_words.fst
fstinfo $tmpdir/g/empty_words.fst | grep cyclic | grep -w 'y' && 
  echo "Language model has cycles with empty words" && exit 1
rm -rf $tmpdir

echo "*** Succeeded in formatting data."

