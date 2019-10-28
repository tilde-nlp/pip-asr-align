#!/usr/bin/env python

import sys


def toHMS(tm):
    tm = tm.split(".")
    seconds = int(tm[0])
    msec = int(tm[1])
    hours = seconds / 3600
    minutes = (seconds / 60) % 60
    seconds = seconds % 60
    return "%02d:%02d:%02d,%03d" % (hours, minutes, seconds, msec)


# S0-part_0005.580-0008.370
count = 1
speaker_id_new = 0
spk_id_map = {}

mode = sys.argv[1].split(",")

for line in sys.stdin:
    subtitle = line.strip().split()
    timemark = subtitle[0]

    subtitle = subtitle[1:]
    if len(subtitle) == 0:
        # skip empty segments
        continue

    if len(subtitle) == 0:
        continue

    speaker_id = int(timemark.split('-')[0][1:])

    if not (spk_id_map.has_key(speaker_id)):
        speaker_id_new += 1
        spk_id_map[speaker_id] = speaker_id_new

    speaker_id_str = "R" + str(spk_id_map[speaker_id])

    timemark = timemark.split('-')[1:]
    timemark[0] = timemark[0].split('_')[1]

    print count
    print "%s --> %s" % (toHMS(timemark[0]), toHMS(timemark[1]))
    if "speakers" in mode:
        print " ".join([speaker_id_str + ":"] + subtitle)
    else:
        print " ".join(subtitle)
    print ""

    count = count + 1
