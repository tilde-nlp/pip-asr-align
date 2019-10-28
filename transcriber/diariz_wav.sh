#!/bin/bash

. ./path.sh
. ./cmd.sh

wavfile=$1
skipdiariz=$2
wavBase=`basename $wavfile .wav`
segfile=$wavBase.seg
logfile=$wavBase.log
data=data/diarization

rm -rf $data

mkdir -p $data

dur=`sox $wavfile -n stat 2>&1 | grep "Length" | awk '{print $3}' | xargs printf "%.2f" | sed "s/\.//"`

if $skipdiariz; then

  echo "--Skip segmentation--"    
  echo "diariz $wavfile" > $data/wav.scp
  echo "spk1-part_1 spk1" > $data/utt2spk
  echo "spk1-part_1 diariz 0 $dur"
  echo "diariz file A" > $data/reco2file_and_channel

else
  echo "--Start segmentation--"    
  /usr/bin/java -Xmx2024m -jar lium/lium_spkdiarization-8.4.1.jar \
   --fInputMask=$wavfile --sOutputMask=$segfile --doCEClustering  $wavBase &>> $logfile
    
  if [ ! -s $segfile ]; then
    echo "XXX XXX 0 $dur XXX XXX XXX S0" > $segfile
  fi

  grep -v ";;" $segfile | cut -f 3,4,8 -d " " | \
  while read LINE ; do \
    start=`echo $LINE | cut -f 1 -d " " | perl -npe '$_=$_/100.0'`;
    len=`echo $LINE | cut -f 2 -d " " | perl -npe '$_=$_/100.0'`;
    sp_id=`echo $LINE | cut -f 3 -d " "`;
    end=`echo "$start $len" | perl -ne '@t=split(); $start=$t[0]; $len=$t[1]; $end=$start+$len; printf("%8.3f\n", $end);'` ;
    timeformatted=`echo "$start $len" | perl -ne '@t=split(); $start=$t[0]; $len=$t[1]; $end=$start+$len; printf("%08.3f-%08.3f\n", $start,$end);'` ;
    echo "${sp_id}-part_${timeformatted} diariz $start $end" >> $data/segments
    echo "${sp_id}-part_${timeformatted} ${sp_id}" >> $data/utt2spk
    #sox build/audio/base/$*.wav --norm $@/$*_$${timeformatted}_$${sp_id}.wav trim $$start $$len ; \
  done
    
  echo "diariz $wavfile" > $data/wav.scp
  echo "diariz file A" > $data/reco2file_and_channel

fi

# Sort files

export LC_ALL=C

sort -o $data/utt2spk $data/utt2spk 
sort -o $data/segments $data/segments

utils/utt2spk_to_spk2utt.pl < $data/utt2spk > $data/spk2utt

echo "--Segmentation done--" >> $logfile


exit 0;
