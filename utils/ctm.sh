#!/bin/bash

lattice=$1 #exp/nnet2_online/nnet_a/decode/lat.1.gz
model=$2 #exp/nnet2_online/nnet_a_online/smbr_epoch3.mdl
wb_file=$3 #data/lang_general_rescore/phones/word_boundary.int
am=$(dirname "${model}")

#export PATH=$PATH:/data/build/kaldi-trunk/src/latbin

if [ -f $am/frame_subsampling_factor ]; then
    factor=$(cat $am/frame_subsampling_factor) || exit 1
    frame_shift="0.0$factor"
else
    frame_shift=0.01
fi


lattice-1best --lm-scale=12 "ark:gunzip -c $lattice |" ark:- |\
lattice-align-words --output-error-lats=false $wb_file $model ark:- ark:- |\
#lattice-align-words-lexicon data/lang_tmp/phones.bak/align_lexicon.int $model ark:- ark:- |\
nbest-to-ctm --frame-shift=$frame_shift ark:- - |\
awk '{split($1,x,"-"); split(x[2],y,"_"); print y[2]+0" "NR" "$0}' |\
sort -n -s -k1,1 |\
awk '{for (i=3; i<NF; i++) printf $i" "; print $NF}'
