import os
import sys
from collections import defaultdict
from align_ids import decode_fname

# create Kaldi dataset from raw ASR transcripts


def to_sec(hms):
    hms = hms.split(",")
    msec = float(hms[1]) / 1000
    hms = hms[0].split(":")
    sec = int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
    return float(sec + msec)

def create_corpus_seg():
    cname = None
    seg = 0
    corpus_size = 0
    thresh = 10 # 10 chars or more
    ali=open("word_alignment","w")
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        name = decode_fname(fname)
        if cname != name:
            seg = 0
            cname = name
        if not os.path.exists("asr/%s.srt" % fname):
            print "No srt file for %s" % fname
            continue
        srt = open("asr/%s.srt" % fname, "r")
        i = 1
        for l_srt in srt:
            if i % 4 == 3:                
                text = l_srt.strip()
                words = text.split()[1:] # skip speaker id
                wbeg = 0
                wlen = 0
                clen = 0
                for w_i in xrange(len(words)):
                    if words[w_i] != "<GARB>" and not any(char.isdigit() for char in words[w_i]):
                        wlen += 1
                        clen += len(words[w_i])
                        if wlen == 1:
                            wbeg = w_i
                    else:
                        if clen >= thresh:
                            ali.write("%s.txt %d %d %d\n" % (cname, seg, wbeg, wlen) )
                        wlen = 0
                        clen = 0
                if clen >= thresh:
                    ali.write("%s.txt %d %d %d\n" % (cname, seg, wbeg, wlen) )
                seg += 1
            i += 1

    print "Wrote alignments to word_alignment"


create_corpus_seg()
