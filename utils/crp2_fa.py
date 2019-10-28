import os
import sys
from collections import defaultdict

# update crp2 Kaldi dataset with FA transcripts


def sort_utt(a,b):  
     utt_id1 = a[0].split("-")
     aseg = int(utt_id1[2])
     astart = int(utt_id1[3])

     utt_id2 = b[0].split("-")
     bseg = int(utt_id2[2])
     bstart = int(utt_id2[3])

     if bseg > aseg:
        return -1
     elif aseg > bseg:
        return 1
     elif bstart > astart:
        return -1
     else:
        return 1      
     return 0

def update_corpus_seg(fa_wavs, fa_text):
    out_wavs=[]
    wavs = [x.strip().split() for x in open("crp2/wav.scp", "r").readlines()]
    text = [x.strip().split() for x in open("crp2/text", "r").readlines()]
    wavs.sort(cmp=sort_utt)
    text.sort(cmp=sort_utt)
    out_text=[]
    i = 0
    prev_i = -1
    prev_start = 0
    prev_wc = 0
    fa_i = 0
    crp2_done = False
    fa_done = False
    # two paralel cycles inside crp2/texts and texts from FA
    while i < len(text) and fa_i<len(fa_text):
        if i < len(text):
            if prev_i != i:
                # parse utt_id of crp2 text
                t = text[i]
                utt_id = t[0].split("-")
                words = t[1:]
                seg = int(utt_id[-2])
                start = int(utt_id[-1])
                wc = len(words)
                prev_i = i 
        else:
            crp2_done =  True
        
        if fa_i < len(fa_text):
            # parse utt_id of FA text
            t = fa_text[fa_i]
            fa_utt_id = t[0].split("-")
            fa_words = t[1:]
            fa_seg = int(fa_utt_id[-3])
            fa_end = int(fa_utt_id[-1])
            fa_start = int(fa_utt_id[-2])
        else:
            fa_done = True

        if prev_wc > 0:
            if crp2_done or seg != prev_seg or prev_start + prev_wc != start:
                # gap still present, print previous
                out_text.append(["-".join(prev_utt_id)] + prev_words)
                out_wavs.append(wavs[i-1])
            else:
                words = prev_words + words
                w1 = float(wavs[i][-3])
                wav_len = float(wavs[i][-2])
                w2 = float(wavs[i-1][-3])
                wavs[i][-2] = str((w1-w2)+wav_len)
                wavs[i][-3] = wavs[i-1][-3]
            prev_wc = 0 #clean

        if not fa_done and (crp2_done or fa_seg < seg):
            out_text.append(fa_text[fa_i])
            out_wavs.append(fa_wavs[fa_i])
            fa_i += 1
            continue
        elif not crp2_done and (fa_done or fa_seg > seg):
            i += 1
            prev_seg = seg
            prev_start = start
            prev_words = words
            prev_utt_id = utt_id
            prev_wc = len(words)
            continue       

        if fa_start < start and fa_end == start:
            words = fa_words + words
            w1 = float(wavs[i][-3])
            w2 = float(fa_wavs[fa_i][-3])
            wav_len = float(wavs[i][-2])
            wavs[i][-2] = str((w1-w2)+wav_len)
            wavs[i][-3] = fa_wavs[fa_i][-3]
            fa_i += 1
            continue
        elif fa_start == start + wc:
            words = words + fa_words
            wav_len = float(wavs[i][-2])
            fa_len = float(fa_wavs[fa_i][-2])
            wavs[i][-2] = str(wav_len+fa_len)
            fa_i += 1
            continue
        else:
            i += 1
            prev_seg = seg
            prev_start = start
            prev_words = words
            prev_utt_id = utt_id
            prev_wc = len(words)

    with open("crp2fa/text","w") as f:
       for x in out_text:
           f.write(" ".join(x)+"\n")
    with open("crp2fa/utt2spk","w") as f:
       for x in out_text:
           utt_id = x[0].split("-")
           spk = utt_id[0]
           f.write("%s %s\n"%(x[0], spk))
    with open("crp2fa/wav.scp","w") as f:
       for x in out_wavs:
           f.write(" ".join(x)+"\n")
    print "Merged FA with CRP2"

if __name__ == "__main__":
    fa_wavs=[x.strip().split() for x in open(sys.argv[1],"r").readlines()]
    fa_text=[x.strip().split() for x in open(sys.argv[2],"r").readlines()]
    
    fa_wavs.sort(cmp=sort_utt)
    fa_text.sort(cmp=sort_utt)

    update_corpus_seg(fa_wavs, fa_text)
