#!/bin/bash

# Copyright 2012 Vassil Panayotov
# Apache 2.0

# The second part of this script comes mostly from egs/rm/s5/run.sh
# with some parameters changed

. ./path.sh

# If you have cluster of machines running GridEngine you may want to
# change the train and decode commands in the file below
. ./cmd.sh

# The number of parallel jobs to be started for some parts of the recipe
# Make sure you have enough resources(CPUs and RAM) to accomodate this number of jobs
cjob=$1
njobs=$2


utils/filter_scp.pl data/crp_fa/split$njobs/$cjob/feats.scp fst.scp > data/crp_fa/split$njobs/$cjob/fst.scp


frame_subsampling_opt=
if [ -f am/frame_subsampling_factor ]; then
  # e.g. for 'chain' systems
  frame_subsampling_opt="--frame-subsampling-factor=$(cat am/frame_subsampling_factor)"
fi

graph=scp,p:data/crp_fa/split$njobs/$cjob/fst.scp
model=am/final.mdl

feats="apply-cmvn --norm-means=false --norm-vars=false --utt2spk=ark:data/crp_fa/split$njobs/$cjob/utt2spk scp:data/crp_fa/split$njobs/$cjob/cmvn.scp scp:data/crp_fa/split$njobs/$cjob/feats.scp ark:- |"


online_ivector_dir=data/crp_fa/ivectors
if [ ! -z "$online_ivector_dir" ]; then
  ivector_period=$(cat $online_ivector_dir/ivector_period) || exit 1;
  ivector_opts="--online-ivectors=scp:$online_ivector_dir/ivector_online.scp --online-ivector-period=$ivector_period"
fi
  
nnet3-latgen-faster \
     $frame_subsampling_opt \
     --config=conf/fa_decode.conf --allow-partial=true \
     --word-symbol-table=data/lang_tmp/words.txt \
     $ivector_opts \
     "$model" \
     $graph "ark,s,cs:$feats" "ark:|lattice-scale --acoustic-scale=10 ark:- ark:- | gzip -c >am/decode/lat.$cjob.gz"  

 
exit 0;
