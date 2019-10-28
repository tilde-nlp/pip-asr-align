#!/bin/bash

# Copyright 2017 Tilde

# Creates graphs per utterance

source path.sh

dictdata=am/dict
acmodel=am
dynamic_scp=false
mk_opts=
stage=0
finalstage=100

. utils/parse_options.sh

if [ $# != 2 ]; then
  echo "Usage: $0 <fst-in-directory> <fst-out-directory>";
  exit 1;
fi

FST_IN_DIR=$1
FST_OUT_DIR=$2



# Process FSTs in directory FST_IN_DIR and create HCLGs in directory FST_OUT_DIR
# Also outputs scm file for FSTs to stdout

if [ $stage -le 1 ] && [ $finalstage -ge 1 ]; then

#create scm
for fst_file in $FST_IN_DIR/*.fst; do
  fst_id=`basename $fst_file .fst`
  fst_id=`echo $fst_id | sed 's/[)(]//g'`
  if $dynamic_scp; then
      echo "$fst_id local/create_graph.sh '$fst_file' $FST_OUT_DIR |"; 
  else
      echo "$fst_id $FST_OUT_DIR/$fst_id/HCLG.fst"; 
  fi
done > fst.scp

export LC_ALL=C
sort -o fst.scp fst.scp

fi

if [ $stage -le 2 ] && [ $finalstage -ge 2 ]; then

# First process each FST to create lexicon.txt and words.txt
# get vocab from FST
mkdir -p data/dict_tmp
for f in extra_questions.txt nonsilence_phones.txt optional_silence.txt silence_phones.txt; do
    cp -r $dictdata/$f data/dict_tmp
done

echo -e "<GARB>\tSL_GARB" > data/dict_tmp/lexicon.txt

fi

if [ $stage -le 3 ] && [ $finalstage -ge 3 ]; then

for fst_file in $FST_IN_DIR/*.fst; do
  cat $fst_file | ../utils/text/dict.py | cut -f1 |\
  grep -E -v "^<.*>$" |\
  ../utils/g2p/g2p.py lt >> data/dict_tmp/lexicon.txt
done

# remove duplicates from lexicon
sort data/dict_tmp/lexicon.txt | uniq > tmp.lex.sort
mv tmp.lex.sort data/dict_tmp/lexicon.txt 

rm data/dict_tmp/lexiconp.txt
rm -rf data/lang_tmp

fi

if [ $stage -le 4 ] && [ $finalstage -ge 4 ]; then

cat data/dict_tmp/lexicon.txt | python -c "
import sys
for line in sys.stdin.readlines():
  sline=line.strip().split()
  if len(sline) >= 2:
    print line.strip()
  else:
    print sline[0] + ' SL_SIL'
" > tmp.lex

mv tmp.lex data/dict_tmp/lexicon.txt 

utils/prepare_lang.sh data/dict_tmp '<GARB>' data/dict_tmp/lang data/lang_tmp || exit 1

# save space
mv data/lang_tmp/phones data/lang_tmp/phones.bak
mkdir data/lang_tmp/phones
cp data/lang_tmp/phones.bak/disambig.int data/lang_tmp/phones.bak/silence.csl data/lang_tmp/phones

fi

if [ $stage -le 5 ] && [ $finalstage -ge 5 ]; then

for fst_file in $FST_IN_DIR/*.fst; do

fst_id=`basename $fst_file .fst`
fst_id=`echo $fst_id | sed 's/[)(]//g'`

cat $fst_file | fstcompile --isymbols=data/lang_tmp/words.txt \
    --osymbols=data/lang_tmp/words.txt  --keep_isymbols=false --keep_osymbols=false | \
  fstrmepsilon | fstarcsort --sort_type=ilabel > data/lang_tmp/G.fst
fstisstochastic data/lang_tmp/G.fst


rm -rf data/lang_tmp/tmp

utils/mkgraph.sh $mk_opts data/lang_tmp $acmodel $FST_OUT_DIR/$fst_id

rm $FST_OUT_DIR/$fst_id/words.txt

done

fi
