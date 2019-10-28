import os
import sys
from collections import defaultdict
from datetime import date
import pickle
from subprocess import Popen, PIPE
import re
from align_ids import decode_fname


def to_sec(hms):
    hms = hms.split(",")
    msec = float(hms[1]) / 1000
    hms = hms[0].split(":")
    sec = int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
    return float(sec + msec)


def create_corpus():
    # load alignment
    ali = dict()
    for line in open("force_alignment","r"):
        line = line.strip().split()
        if line[0][:-4] not in ali:
            ali[line[0][:-4]] = defaultdict(list)
        ali[line[0][:-4]][int(line[1])].append((int(line[2]), int(line[3]), " ".join(line[5:])))
    cname = None
    seg = 0
    corpus_size = 0
    textfile=open("crp_fa/text","w")
    utt2spk=open("crp_fa/utt2spk","w")
    wavscp=open("crp_fa/wav.scp","w")
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        name = decode_fname(fname)
        if cname != name:
            seg = 0
            cname = name
        srt = open("asr/%s.srt" % fname, "r")
        ctm = open("asr/%s.ctm" % fname, "r").readlines()
        ctm_i = 0
        i = 1
        for l_srt in srt:
            if i % 4 == 3:
                text = l_srt.strip().split()
                if cname in ali and seg in ali[cname]:
                    # get speaker id
                    speaker = "spk%s%s" % (cname, text[0][:-1])
                    speaker = speaker.replace("(","").replace(")","")
                    # loop through all alignments
                    lastword = 0
                    for (start, end, fa_text) in ali[cname][seg]:
                        # get utterance id
                        utt_id = "part-%s-%s-%s" % (seg, start, end)
                        # read ctm timings
                        ctmline = ctm[ctm_i+start].strip().split()
                        tmp = ctmline[0]
                        begin = float(ctmline[2])
                        ctmline = ctm[ctm_i+end-1].strip().split()
                        if tmp != ctmline[0]:
                            print "CTM misalignment found!"
                            print cname, seg, start, end, ctmline
                        end = float(ctmline[2]) + float(ctmline[3])
                        # add segment offset
                        begin += parseCtmSegName(ctmline[0])
                        end += parseCtmSegName(ctmline[0])
                        # write corpus
                        corpus_size += end-begin
                        textfile.write("%s-%s %s\n" % (speaker, utt_id, fa_text))
                        utt2spk.write("%s-%s %s\n" % (speaker, utt_id, speaker))
                        wavscp.write("%s-%s sox '../audio/%s' -r 16k -t wav - trim %s %s |\n" % (speaker, utt_id, fname, begin, end-begin))
                        # write fst
                        create_fst("%s-%s" % (speaker, utt_id), fa_text)
                else:
                    tmp = ctm[ctm_i].strip().split()[0]

                # advance ctm_i to the next segment
                c = ctm_i
                while ctm_i < len(ctm):
                    if ctm[ctm_i].strip().split()[0] != tmp:
                        break
                    ctm_i += 1

                # mismatch between ctm segment len and srt text len
                # NB: text contains speakers id, so we need to account for that
                #     (hence: len -1)
                if (ctm_i-c) != (len(text)-1):
                    print(fname,seg+1)
                    print("text: %d, ctm: %d" % ((len(text)-1),(ctm_i-c)))
                seg += 1
            i += 1

    print "Created corpus of size: " + str(corpus_size)


def create_fst_nogarb(fst_id, text):
    i = 0
    with open("crp_fa/fsts/%s.fst" % fst_id, "w") as f:
        for word in text.split():
            f.write("0 %d %s %s\n" % (i+1, word, word)) # it can be reached from utt start
            i += 1
        j = 1
        for word in text.split():
            if j > 1:
                f.write("%d %d %s %s\n" % (j-1, j, word, word)) # it can be reached from prev
                f.write("%d\n" % (j-1)) # prev a terminating state
            j += 1
        f.write("%d\n" % (j-1)) # last 

def create_fst(fst_id, text):
    i = 0
    with open("crp_fa/fsts/%s.fst" % fst_id, "w") as f:
        f.write("0 0 <GARB> <GARB>\n") # garb loop at the start
        for word in text.split():
            f.write("0 %d %s %s\n" % (i+1, word, word)) # it can be reached from utt start
            i += 1
        j = 1
        for word in text.split():
            if j > 1:
                f.write("%d %d %s %s\n" % (j-1, j, word, word)) # it can be reached from prev
                f.write("%d\n" % (j-1)) # prev a terminating state
            f.write("%d %d <GARB> <GARB>\n" % (j, j)) # garb loop
            j += 1
        f.write("%d\n" % (j-1)) # last 

def iosymbols(fst_id):
    with open("crp_fa/fsts/%s.fst" % fst_id, "r") as f:
        with open("symbols", "w") as fsym:
            words = dict()
            for line in f:
                line = line.split()
                if len(line) > 1:
                    words[line[-2]] = 1
            i = 0
            for w in words:
                fsym.write("%s %d\n" % (w, i))
                i += 1

def parseCtmSegName(segName):
    #S103-part_0000.030-0002.010
    parse = segName.split("_")[-1].split("-")
    return float(parse[0])
        
if len(sys.argv) == 2:
    stage = int(sys.argv[1])
else:
    stage = 1

if stage <= 0:
    # debug
    iosymbols("spk20111018R1-part-79-0")

if stage <= 1:
    create_corpus()
