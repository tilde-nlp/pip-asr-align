#!/bin/bash

. ./path.sh
. ./cmd.sh

# The number of parallel jobs to be started for some parts of the recipe
# Make sure you have enough resources(CPUs and RAM) to accomodate this number of jobs
njobs=$1

am=am
iter=final
lm=lm
align_asr_dir=..
decode_dir=$am/decode
rescore_dir=$am/decode_rescore
wboundary=$lm/phones/word_boundary.int
word_symbol_table=$lm/words.txt
if [ -f $am/frame_subsampling_factor ]; then
    factor=$(cat $am/frame_subsampling_factor) || exit 1
    frame_shift="0.0$factor"
else
    frame_shift=0.01
fi
lmwt=12

. utils/parse_options.sh

# get CTM and SRT
echo "--Generating SRT and CTM--"

lattice-best-path --lm-scale=$lmwt --word-symbol-table=$word_symbol_table \
    "ark:gunzip -c $rescore_dir/lat.*.gz|" ark,t:best.tra

./utils/int2sym.pl -f 2- $word_symbol_table < best.tra | sort > best.txt #|\

mkdir -p srt

cat best.txt |\
    sort -t"_" -k2n | $align_asr_dir/utils/step1_to_srt.py full,speakers | sed 's/$/\r/' > srt/diariz.srt


lattice-align-words --output-error-lats=false $wboundary $am/$iter.mdl "ark:gunzip -c $rescore_dir/lat.*.gz|" ark:- |\
lattice-to-ctm-conf --decode_mbr=false --confidence-digits=3 --frame-shift=$frame_shift ark:- ark,t:best.tra - |\
awk '{split($1,x,"-"); split(x[2],y,"_"); print y[2]+0" "NR" "$0}' |\
sort -n -s -k1,1 |\
awk '{for (i=3; i<NF; i++) printf $i" "; print $NF}' > srt/diariz.ctm

rm best.txt best.tra
