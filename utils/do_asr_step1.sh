#!/bin/bash

. ./setup.sh
dir_with_files=$1

rm id.lst

for sound_file in $dir_with_files/*.mp3; do
     echo "--Doing ASR for ${sound_file}--"
     name=`basename $sound_file .mp3`

     echo "--Converting to wav--"
     # convert to 16kHz WAV
     sox $sound_file -r 16k -t wav $KALDI_DIR/$name.wav
     
     # diarization
     cd $KALDI_DIR
     ./diariz_wav.sh $name.wav false

     # decode and generate SRT/CTM
     ./step1_decode.sh $STEP1_DECODE_JOBS

     cd ..
     # copy SRT and CTM files and update id.lst
     mv transcriber/srt/diariz.srt asr/$name.mp3.srt
     mv transcriber/srt/diariz.ctm asr/$name.mp3.ctm 
     echo "$name.mp3" >> id.lst
     
     # cleanup
     rm $KALDI_DIR/$name.wav
done

