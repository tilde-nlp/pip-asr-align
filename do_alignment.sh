#!/bin/bash

# this script assumes that audio is placed in "audio" directory
# and unnormalized text transcriptions are placed in "text"
# the files in "audio" and "text" directories should have the 
# same names, that differ only in extension

lang=$1
stage=$2

# load environment variables
. ./setup.sh

mkdir -p asr
mkdir -p parts
mkdir -p ref
mkdir -p crp1
mkdir -p crp2

if [ $stage -le 1 ]; then
    # normalize ref transcripts
    utils/$lang/normalize.sh
fi


if [ $stage -le 2 ]; then
    # create biased LM
    # TODO: here you can train biased LM on the reference texts
    echo "skip"
fi


if [ $stage -le 3 ]; then
    # decode 
    utils/do_asr_step1.sh audio
fi

if [ $stage -le 4 ]; then
    # prepare for align
    python utils/prepare_align.py 2
fi

if [ $stage -le 5 ]; then
    # align and create corpus
    python utils/align_files.py
fi

# =====================================
# perform pseudo-force alignment
# =====================================

if [ $stage -le 6 ]; then
    echo "--Creating FA_CORPUS--"
    # create fa_corpus
    rm -rf crp_fa $KALDI_DIR/data/crp_fa
    mkdir -p crp_fa
    mkdir -p crp_fa/fsts
    mkdir -p $KALDI_DIR/data/crp_fa
    python utils/fa_corpus.py

    # copy crp_fa to Kaldi system
    cp crp_fa/* $KALDI_DIR/data/crp_fa
fi

if [ $stage -le 7 ]; then
    echo "--Extracting features--"
    # go to Kaldi dir
    cd $KALDI_DIR
    # prepare data set
    local/prepare_align_set.sh --njobs $FA_DECODE_JOBS data/crp_fa
    cd ..
fi


if [ $stage -le 8 ]; then
    echo "--Creating FA FSTs--"
    # go to Kaldi dir
    cd $KALDI_DIR
    mkdir -p fa_fsts
    # execute create graphs script in the system local\
    ../utils/$lang/create_graphs.sh --mk-opts "$MKGRAPH_OPTS" --dynamic_scp true --finalstage 4 ../crp_fa/fsts fa_fsts
    cd ..
fi

if [ $stage -le 9 ]; then
    cd $KALDI_DIR
    for i in $(seq 1 $FA_DECODE_JOBS)
    do
        # decode
        ../utils/fa_nnet3_decode_job.sh $i $FA_DECODE_JOBS &
    done
    wait
    cd ..
fi

if [ $stage -le 10 ]; then
    rm -rf crp2fa
    mkdir crp2fa
    cd $KALDI_DIR
    # get CTM and SRT
    echo "--Getting SRT/CTM from FA decode--"
    ../utils/decode_to_align.sh --decode false --data_dir data/crp_fa --decode_dir am/decode --align_asr_dir .. --word_symbol_table data/lang_tmp/words.txt --am am/final.mdl --wboundary data/lang_tmp/phones.bak/word_boundary.int
    cd ..
fi

if [ $stage -le 11 ]; then
    # NOT USED
    # merge FA with crp2
    # python utils/crp2_fa.py $KALDI_DIR/data/crp_fa/wav.scp $KALDI_DIR/12.txt 

    # update Step1 ASR results with FA results
    cp -r asr asr.bak
    python utils/update_asr_with_fa.py $KALDI_DIR/all.sorted.ctm $KALDI_DIR/12.txt
    python utils/prepare_align.py 2
    python utils/align_files.py 2,4

    LC_ALL=C sort -o crp2/text crp2/text
    LC_ALL=C sort -o crp2/wav.scp crp2/wav.scp
    LC_ALL=C sort -o crp2/utt2spk crp2/utt2spk

    rm -rf asr.bak
fi

if [ $stage -le 12 ]; then
    # cleanup
    rm -rf $KALDI_DIR/12.tra $KALDI_DIR/12.txt $KALDI_DIR/all*.ctm $KALDI_DIR/data/crp_fa $KALDI_DIR/fa_fsts $KALDI_DIR/mfcc $KALDI_DIR/srt 
    rm $KALDI_DIR/fst.scp
fi
