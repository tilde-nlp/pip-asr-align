import os
import sys
from collections import defaultdict
from align_ids import decode_fname

# update Step1Decode result with FA transcripts

def update_asr(fa_ctm, fa_text):
    seg = 0
    cname = None
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        name = decode_fname(fname)
        if cname != name:
            seg = 0
            cname = name
        srt = open("asr.bak/%s.srt" % fname, "r")
        o_srt = open("asr/%s.srt" % fname, "w")
        ctm = open("asr.bak/%s.ctm" % fname, "r").readlines()
        o_ctm = open("asr/%s.ctm" % fname, "w")
        ctm_i = 0
        i = 1
        for l_srt in srt:
            if i % 4 == 3:
                text = l_srt.strip().split()
                speaker = text[0]
                text = text[1:]
                wc = len(text)
                offset = 0
                ctm_skip = 0                
                for w in xrange(wc):
                    if cname in fa_text and seg in fa_text[cname] and w in fa_text[cname][(seg)]:
                        end, fa = fa_text[cname][seg][w]
                        fa = fa[1:]
                        text = text[:w+offset] + fa + text[end+offset:]
                        offset += len(fa) - (end-w)
                        ctm_line = ctm[ctm_i].strip().split()
                        start = float(ctm_line[2])
                        if w not in fa_ctm[cname][seg]:
                            fa_ctm[cname][seg][w] = []
                        for fa_ctm_line in fa_ctm[cname][seg][w]:
                            fa_start = float(fa_ctm_line[2])
                            fa_end = fa_ctm_line[3]
                            ctm_line[2] = str(start + fa_start)
                            ctm_line[3] = fa_end 
                            ctm_line[4] = fa_ctm_line[4]
                            o_ctm.write(" ".join(ctm_line)+"\n")
                        ctm_skip = end - w
                    
                    if ctm_skip == 0:
                        o_ctm.write(ctm[ctm_i])
                    else:
                        ctm_skip -= 1
                    ctm_i += 1
                l_srt = speaker + " " + " ".join(text) + "\n"
                seg += 1
            
            o_srt.write(l_srt)
            i += 1
        o_srt.close()
        o_ctm.close()

    print "Merged FA with step1 ASR decode"

if __name__ == "__main__":
    fa_ctm=[x.strip().split() for x in open(sys.argv[1],"r").readlines()]

    fa_ctm_dict=dict()
    for x in fa_ctm:
        utt_id1 = x[0].split("-")
        aseg = int(utt_id1[2])
        astart = int(utt_id1[3])
        Rdelim = utt_id1[0].find("R")
        cname = utt_id1[0][3:Rdelim]
        if cname not in fa_ctm_dict:
            fa_ctm_dict[cname]=dict()
        if aseg not in fa_ctm_dict[cname]:
            fa_ctm_dict[cname][aseg]=dict()
        if astart not in fa_ctm_dict[cname][aseg]:
            fa_ctm_dict[cname][aseg][astart]=list()
        fa_ctm_dict[cname][aseg][astart].append(x)
        

    fa_text=[x.strip().split() for x in open(sys.argv[2],"r").readlines()]
    
    fa_text_dict=dict()
    for x in fa_text:
        utt_id1 = x[0].split("-")
        aseg = int(utt_id1[2])
        astart = int(utt_id1[3])
        aend = int(utt_id1[4])
        Rdelim = utt_id1[0].find("R")
        cname = utt_id1[0][3:Rdelim]
        if cname not in fa_text_dict:
            fa_text_dict[cname]=dict()
        if aseg not in fa_text_dict[cname]:
            fa_text_dict[cname][aseg]=dict()
        fa_text_dict[cname][aseg][astart]=(aend, x)

    update_asr(fa_ctm_dict, fa_text_dict)
