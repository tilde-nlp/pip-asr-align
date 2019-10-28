#!/bin/bash

. ./path.sh
. ./cmd.sh

# The number of parallel jobs to be started for some parts of the recipe
# Make sure you have enough resources(CPUs and RAM) to accomodate this number of jobs
njobs=$1


am=am
iter=final
graph=graph
data_dir=data/diarization
lm=lm
decode_dir=$am/decode
rescore_dir=$am/decode_rescore

. utils/parse_options.sh

# decode
echo "--Decoding--"
steps/online/nnet3/decode.sh --iter $iter --do_endpointing false --skip_scoring true --acwt 1.0 --post-decode-acwt 10 --nj $njobs --online false --config conf/decode.conf ${am}/$graph $data_dir $decode_dir

# rescore
echo "--Rescoring--"
steps/lmrescore_const_arpa.sh --skip_scoring true $lm $lm $data_dir $decode_dir $rescore_dir

# get CTM and SRT
./get_ctm_srt.sh
