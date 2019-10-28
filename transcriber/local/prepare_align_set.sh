#!/bin/bash

# The second part of this script comes mostly from egs/rm/s5/run.sh
# with some parameters changed

. ./path.sh

# If you have cluster of machines running GridEngine you may want to
# change the train and decode commands in the file below
. ./cmd.sh

# The number of parallel jobs to be started for some parts of the recipe
# Make sure you have enough resources(CPUs and RAM) to accomodate this number of jobs
njobs=4
extract_feats=true

. utils/parse_options.sh


data=$1

# Sort files
export LC_ALL=C
sort -o $1/text $1/text
sort -o $1/wav.scp $1/wav.scp
sort -o $1/utt2spk $1/utt2spk
if [ -f $1/segments ]; then
    sort -o $1/segments $1/segments
fi

# create spk2utt
utils/utt2spk_to_spk2utt.pl < $1/utt2spk > $1/spk2utt
sort -o $1/spk2utt $1/spk2utt


# features
if [ "$extract_feats" = true ] ; then
  steps/make_mfcc.sh --cmd "$train_cmd" --nj $njobs --mfcc-config conf/mfcc.conf \
	   $1 exp/make_mfcc/align_set mfcc || exit 1;
  steps/compute_cmvn_stats.sh $1 exp/make_plp/align_set mfcc || exit 1;

  steps/online/nnet2/extract_ivectors_online.sh --nj $njobs \
      $data  am/ivector_extractor $data/ivectors
fi

# utt2dur
cut -d" " -f1 $1/text | paste -d" " - <( cut -d" " -f11 $1/wav.scp) > $1/utt2dur

