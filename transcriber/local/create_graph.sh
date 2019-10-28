#!/bin/bash

# Copyright 2017 Tilde

# Creates graph from utterance FST

source path.sh

acmodel=am
mk_opts=

. utils/parse_options.sh

if [ $# != 2 ]; then
  echo "Usage: $0 <fst-in> <fst-out-directory>";
  exit 1;
fi

fst_file=$1
FST_OUT_DIR=$2


fst_id=`basename $fst_file .fst`
fst_id=`echo $fst_id | sed 's/[)(]//g'`

mkdir -p data/lang_tmp_$fst_id

cp data/lang_tmp/* data/lang_tmp_$fst_id 2> $FST_OUT_DIR/$fst_id.log
cp -r data/lang_tmp/phones data/lang_tmp_$fst_id

fstcompile --isymbols=data/lang_tmp/words.txt \
    --osymbols=data/lang_tmp/words.txt  --keep_isymbols=false --keep_osymbols=false $fst_file data/lang_tmp_$fst_id/tmp.fst

fstrmepsilon data/lang_tmp_$fst_id/tmp.fst data/lang_tmp_$fst_id/tmp2.fst

fstarcsort --sort_type=ilabel data/lang_tmp_$fst_id/tmp2.fst data/lang_tmp_$fst_id/G.fst

utils/mkgraph.sh $mk_opts data/lang_tmp_$fst_id $acmodel $FST_OUT_DIR/$fst_id >>$FST_OUT_DIR/$fst_id.log 2>&1

cat $FST_OUT_DIR/$fst_id/HCLG.fst | fstconvert --fst_type=vector

rm -rf data/lang_tmp_$fst_id
rm -rf $FST_OUT_DIR/$fst_id
