#!/bin/bash

# Performs Kaldi decoding of the corpus
# And prepares SRT, CTM files for next align steps
# To be run from Kaldi system directory

. ./cmd.sh

. ./path.sh


decode=true
decode_rescore=true
data_dir=data/saeima11_alldata
rescore_lang=data/lang_general_rescore
decode_dir=exp/nnet2_online/nnet_a_online/decode
decode_graph=exp/nnet2_online/tri3b/graph
word_symbol_table=${decode_graph}/words.txt
align_asr_dir=../../align-asr
am=exp/nnet2_online/nnet_a_online/smbr_epoch3.mdl
wboundary=data/lang_general_rescore/phones/word_boundary.int
lmwt=12

. utils/parse_options.sh

if [ "$decode" == "true" ]; then

steps/online/nnet2/decode.sh --config conf/decode.conf --iter smbr_epoch3 --nj 6 --online false --cmd "$decode_cmd" \
 $decode_graph $data_dir $decode_dir

if [ "$decode_rescore" == "true" ]; then
steps/lmrescore_const_arpa.sh $rescore_lang $rescore_lang $data_dir $decode_dir ${decode_dir}_rescore

decode_dir=${decode_dir}_rescore
fi

fi


rm all.ctm
for f in $decode_dir/*.gz
do
    $align_asr_dir/utils/ctm.sh $f $am $wboundary >> all.ctm
done


lattice-best-path --lm-scale=$lmwt --word-symbol-table=$word_symbol_table \
    "ark:gunzip -c $decode_dir/lat.*.gz|" ark,t:12.tra

#cp $decode_dir/scoring_kaldi/penalty_1.0/$lmwt.txt 12.txt

./utils/int2sym.pl -f 2- $word_symbol_table < 12.tra | sort > 12.txt #|\
#sort -t"_" -k2n | to_srt.py full,speakers | sed 's/$/\r/' > 12.srt

# for bedu_turgus
#sed -i "s/\(LAI[0-9]\{5\}\)/\1R/" 12.txt
#sed -i "s/\(LAI[0-9]\{5\}\)/\1R/" all.ctm
#sed -i "s/\(LAI[0-9]\{5\}\)R-/\1R1-/" 12.txt
#sed -i "s/\(LAI[0-9]\{5\}\)R-/\1R1-/" all.ctm

mkdir -p srt

sed "s/R/ /;s/-part/ part/" < $data_dir/wav.scp | sort -k 1,1 -k3,3V | sed "s/ /R/;s/ part/-part/" | python $align_asr_dir/utils/to_srt.py


sed "s/R/ /;s/-part/ part/" < all.ctm | sort -k 1,1 -k3,3V -k 5,5n | sed "s/ /R/;s/ part/-part/" > all.sorted.ctm

sed "s/R/ /;s/-part/ part/" < $data_dir/wav.scp | sort -k 1,1 -k3,3V | sed "s/ /R/;s/ part/-part/" | python $align_asr_dir/utils/to_align_ctm.py





