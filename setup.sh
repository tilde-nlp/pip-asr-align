# paths
export KALDI_DIR="./transcriber"
export KALDI_ROOT="/opt/kaldi-trunk"
export KENLM=="/data/build/kenlm"
export SRILM=="/opt/srilm"

# language files
# abbreviation lists, prevents lowering abbreviations during normalization
export ABBR_EXCEPTION_LIST_LV=utils/empty
export ABBR_EXCEPTION_LIST_LT=utils/empty

# decode settings
export STEP1_DECODE_JOBS=2
export MKGRAPH_OPTS="--self-loop-scale 1.0"
export FA_DECODE_JOBS=4


# setup some dependecies and directories

if [ ! -d $KALDI_DIR/steps ]; then
    ln -s $KALDI_ROOT/egs/wsj/s5/steps $KALDI_DIR/steps
fi


if [ ! -d $KALDI_DIR/utils ]; then
    ln -s $KALDI_ROOT/egs/wsj/s5/utils $KALDI_DIR/utils
fi


if [ ! -d $KALDI_DIR/lium ]; then
    wget https://git-lium.univ-lemans.fr/Meignier/lium-spkdiarization/blob/master/jar/lium_spkdiarization-8.4.1.jar.gz

    mkdir $KALDI_DIR/lium

    mv lium_spkdiarization-8.4.1.jar.gz $KALDI_DIR/lium
    gunzip $KALDI_DIR/lium/lium_spkdiarization-8.4.1.jar.gz
fi

