#!/usr/bin/env python

import sys



texts = [x.strip().split() for x in open("12.txt","r").readlines()]
texts = { x[0] : x[1:] for x in texts }

ctms = [x.strip().split()[0] for x in open("all.ctm","r").readlines()]
ctms = set(ctms)


def toHMS(tm):
    tm = float(tm)
    seconds = int(tm)
    msec = (tm - seconds) * 1000
    hours = seconds / 3600
    minutes = seconds / 60
    seconds = seconds % 60
    return "%02d:%02d:%02d,%03d" % (hours,minutes,seconds,msec)


def segidToSpkid(segid):
    #spk20111018R1-part-661-17
    spk = segid.split("R")[1].split("-")[0]
    return spk

count = 1
speaker_id_new = 0
spk_id_map = {}

prev = ""
out = None
for line in sys.stdin:
    line = line.strip().split()
    segid = line[0]
    fname = line[2].split("/")[-1].replace("'","") # take the file part, remove quotes
    begin = line[-3]
    end = line[-2]

    if prev != fname:
       if out:
           out.close()
       out = open("srt/"+fname+".srt","w")
       count = 1
       prev = fname

    # skip empty segments or segments with no ctm
    if segid not in texts or len(texts[segid]) == 0 or segid not in ctms:
        continue

    out.write("%s\n" % count)
    out.write("%s --> %s\n" % (toHMS(begin), toHMS(float(begin)+float(end))))
    out.write("R%s: %s\n" % (segidToSpkid(segid), " ".join(texts[segid])))
    out.write("\n")

    count = count + 1
if out:
    out.close()
