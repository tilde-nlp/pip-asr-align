#!/bin/bash

for vid in vid/*
do
    avconv -i $vid audio/`basename $vid .mp4`.mp3
    rm $vid
done
