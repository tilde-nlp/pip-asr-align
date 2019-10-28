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


#steps/online/nnet2/extract_ivectors_online.sh --nj 4 \
#      data/crp_fa exp/nnet2_online/extractor exp/nnet2_online/ivectors_crp_fa || exit 1;

#local/nnet2/decode_mult_fsts.sh --online_ivector_dir exp/nnet2_online/ivectors_crp_fa \
#      --words_dir data/lang_tmp --nj 1 --cmd "$decode_cmd" \
#      "scp:fst.scp" data/crp_fa exp/nnet2_online/nnet_a/decode

utils/filter_scp.pl data/crp_fa/split$njobs/$cjob/feats.scp fst.scp > data/crp_fa/split$njobs/$cjob/fst.scp

nnet-latgen-faster --minimize=false --max-active=7000 --min-active=200 --beam=15.0 --lattice-beam=8.0 --acoustic-scale=0.1 --allow-partial=true --word-symbol-table=data/lang_tmp/words.txt exp/nnet2_online/nnet_a/final.mdl scp,p:data/crp_fa/split$njobs/$cjob/fst.scp "ark,s,cs:apply-cmvn --norm-means=false --norm-vars=false --utt2spk=ark:data/crp_fa/split$njobs/$cjob/utt2spk scp:data/crp_fa/split$njobs/$cjob/cmvn.scp scp:data/crp_fa/split$njobs/$cjob/feats.scp ark:- | paste-feats --length-tolerance=10 ark:- 'ark,s,cs:utils/filter_scp.pl data/crp_fa/split$njobs/$cjob/utt2spk exp/nnet2_online/ivectors_crp_fa/ivector_online.scp | subsample-feats --n=-10 scp:- ark:- | copy-matrix --scale=1.0 ark:- ark:-|' ark:- |" "ark:|gzip -c > exp/nnet2_online/nnet_a/decode/lat.$cjob.gz" #1>fa_decode2.log 2>&1

#local/score.sh data/crp_fa data/lang_tmp exp/nnet2_online/nnet_a/decode

#/data/Projekti/align-asr-lt/utils/decode_to_align.sh --decode false --data_dir data/crp_fa --decode_dir exp/nnet2_online/nnet_a/decode --align_asr_dir ../../align-asr-lt --word_symbol_table data/lang_tmp/words.txt --am exp/nnet2_online/nnet_a/final.mdl --wboundary data/lang_tmp/phones.bak/word_boundary.int

#gmm-latgen-faster --max-active=7000 --beam=15.0 --lattice-beam=8.0 --acoustic-scale=0.083333 --allow-partial=true --word-symbol-table=data/lang_tmp/words.txt exp/tri2b/final.mdl scp,p:data/crp_fa/split4/$1/fst.scp "ark,s,cs:apply-cmvn  --utt2spk=ark:data/crp_fa/split4/$1/utt2spk scp:data/crp_fa/split4/$1/cmvn.scp scp:data/crp_fa/split4/$1/feats.scp ark:- | splice-feats  ark:- ark:- | transform-feats exp/tri2b/final.mat ark:- ark:- |" "ark:|gzip -c > exp/tri2b/decode/lat.$1.gz" 

#local/score.sh data/crp_fa data/lang_tmp exp/tri2b/decode

#/data/Projekti/align-asr-lt/utils/decode_to_align.sh --decode false --data_dir data/crp_fa --decode_dir exp/tri2b/decode --align_asr_dir ../../align-asr-lt --word_symbol_table data/lang_tmp/words.txt --am exp/tri2b/final.mdl --wboundary data/lang_tmp/phones.bak/word_boundary.int
 
exit 0;
