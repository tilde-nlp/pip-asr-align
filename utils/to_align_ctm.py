#!/usr/bin/env python

import sys



ctms = [x.strip().split() for x in open("all.sorted.ctm","r").readlines()]
#texts = { x[0] : x[1:] for x in texts }

def toHMS(tm):
    tm = tm.split(".")
    seconds = int(tm[0])
    msec = int(tm[1])
    hours = seconds / 3600
    minutes = seconds / 60
    seconds = seconds % 60
    return "%02d:%02d:%02d,%03d" % (hours,minutes,seconds,msec)


def segidToSpkid(segid):
    #spk20111018R1-part-661-17
    spk = segid.split("R")[1].split("-")[0]
    return spk

count = 0

prev = ""
out = None
for line in sys.stdin:
    line = line.strip().split()
    segid = line[0]
    fname = line[2].split("/")[-1].replace("'","") # take the file part, remove quotes
    begin = line[-3]
    end = str(float(line[-2]) + float(begin))

    if prev != fname:
       if out:
           out.close()
       out = open("srt/"+fname+".ctm","w")
       prev = fname

    spkid = "S"+segidToSpkid(segid)
    partid = "-part_%s-%s " % (begin, end)

    while ctms[count][0] == segid:
        out.write(spkid+partid)
        out.write(" ".join(ctms[count][1:]))
        out.write("\n")
        count += 1
        if count >= len(ctms):
            break

if out:
    out.close()
