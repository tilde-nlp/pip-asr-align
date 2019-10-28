import os
import sys
from collections import defaultdict
from datetime import date
import pickle
from subprocess import Popen, PIPE
import re
from align_ids import start_file_align, decode_fname

# perform first step of alignment, for each asr file find corresponding ref file by date

def start_transcript_align():
    file_alignment = pickle.load(open("file_alignment", "r"))
    alignment = open("alignment", "w")
    walignment = open("word_alignment", "w")
    falignment = open("force_alignment", "w")
    progress = 0
    for ref_file in file_alignment:
        progress += 1
        print "Processing file %s (%s of %s)" % (ref_file, progress, len(file_alignment))
        # read ref file
        ref=" ".join(open("ref/"+ref_file, "r").readlines())
        ref=ref.decode("utf-8").lower()
        open("tmp.ref","w").write(ref.encode("utf-8"))
        ref = ref.split()        
        asr=""
        # read and concat asr files
        if len(file_alignment[ref_file]) > 1:
            print ref_file, "has more than 1 ASR transcript !", file_alignment[ref_file]
            return
        for asr_file in file_alignment[ref_file]:
            t=open("parts/"+asr_file, "r").readline().decode("utf-8").lower()
            #t=t.replace("<unk>","").replace("<garb>","")
            asr = asr + t + " "
        open("tmp.asr","w").write(asr.encode("utf-8"))
        asr = asr.split()

        process = Popen(["utils/align.cpp/align","tmp.asr","tmp.ref"], stdout=PIPE, stderr=PIPE)
        ali = process.communicate()[0].split()

        ali_r_pos = int(ali[0])
        ali_q_pos = int(ali[1])
        if len(ali) < 3:
            print "%d (%d%%) from %d from segments aligned" % (0, 0, 0)
            continue
        ali_cigar = ali[2].strip()
        # find good segments
        find_good_segments(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, file_alignment[ref_file][0], alignment)
        # find good word sequences
        find_good_wordseq(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, file_alignment[ref_file][0], walignment)
        # prepare for force alignment
        text_between_anchors(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, file_alignment[ref_file][0], falignment)

    alignment.close()
    walignment.close()
    falignment.close()

def text_between_anchors(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, asr_file_id, alignment):
        thresh = 11 * 2 # threshold in characters, 11 is average word length 
        max_anc_list = 100
        max_seconds_between_anchors = 45
        avg_phone_dur = 0.44 / 11.0
        max_possible_phones = max_seconds_between_anchors / avg_phone_dur
        fa_thresh = 6

        i = 0
        seg = 0
        cigar_op = None
        cigar_i = 0
        j = ali_r_pos
        ali_words = 0

        match_beg = -1
        match_len = 0
        match_len_char = 0
        seg_i = 0

        possible_text = []
        anc_segs = []
        anc_start = None
        anc_end = None

        # NB: currently only cigar from ops with count=1 is supported
        while i < len(asr):
            if len(ali_cigar) < 2:
                break
            if asr[i] == "|" and ali_cigar[1] == 'Y':
                if match_len_char > thresh:
                    # found a match run with sufficient length
                    # found anchor point on the end of segment
                    if anc_start == None:
                        anc_start = (asr_file_id, seg+1, 0, 0)
                        possible_text = []
                    elif anc_end == None:
                        anc_end = (asr_file_id, seg, match_beg, match_len)
                        # align "possible text" and anchored segment
                        if len(possible_text) > fa_thresh:
                            possible_text = (" ".join(possible_text[:-match_len])).encode("utf-8")
                            if len(anc_segs) == 0:
                                if anc_end[2] > anc_start[2] + anc_start[3]:
                                    # save info
                                    alignment.write("%s %d %d %d = %s\n" % 
                                        (asr_file_id, seg, anc_start[2] + anc_start[3], anc_end[2], possible_text))
                                    ali_words += anc_end[2] - anc_start[2] - anc_start[3]
                            else:
                                # assign same possible text to each anc_segs
                                start_seg_i = anc_start[2] + anc_start[3]
                                for anc_seg in anc_segs:
                                    if start_seg_i == anc_seg[1]:
                                        start_seg_i = 0
                                        continue
                                    alignment.write("%s %d %d %d = %s\n" % 
                                        (asr_file_id, anc_seg[0], 
                                         start_seg_i, anc_seg[1], possible_text))
                                    ali_words += anc_seg[1] - start_seg_i
                                    start_seg_i = 0
                                # if we have some unaligned start of seg, add it too
                                if anc_end[2] != 0:
                                    alignment.write("%s %d %d %d = %s\n" % 
                                        (asr_file_id, anc_end[1], 0, anc_end[2], possible_text))   
                                    ali_words += anc_end[2]
                        anc_start = (asr_file_id, seg+1, 0, 0)
                        possible_text = []
                        anc_segs = []
                        anc_end = None
                else:
                    # should we add this segment to the list of "anchored" segments?
                    if anc_start:
                        anc_segs.append((seg, seg_i))
                    if len(anc_segs) > max_anc_list:
                       # discard anchor point
                        anc_start = None
                        anc_segs = []

                # new segment started
                match_len = 0
                match_len_char = 0
                seg += 1
                seg_i = 0
                # skip ali op for delimeter 
                if i >= ali_q_pos:
                    ali_cigar = ali_cigar[2:]                    
                i += 1
            elif i >= ali_q_pos:
                # advance in cigar
                cigar_op = re.search("^1(\w)", ali_cigar)
                if cigar_op is None:
                    break
                op = cigar_op.group(1)
                # remove op from cigar
                ali_cigar = ali_cigar[cigar_op.end(1):]                
                
                # eval cigar op
                if op != "M":
                    if match_len_char > thresh:
                        # found a match run with sufficient length
                        # found anchor point inside(or beginning) segment
                        if anc_start == None:
                            anc_start = (asr_file_id, seg, match_beg, match_len)
                            possible_text = []
                        elif anc_end == None:
                            anc_end = (asr_file_id, seg, match_beg, match_len)
                            # align "possible text" and anchored segment
                            possible_text = (" ".join(possible_text[:-match_len])).encode("utf-8")
                            if len(possible_text) > fa_thresh:
                                if len(anc_segs) == 0:
                                    if anc_end[2] > anc_start[2] + anc_start[3]:
                                        # save info
                                        alignment.write("%s %d %d %d = %s\n" % 
                                            (asr_file_id, seg, anc_start[2] + anc_start[3], 
                                            anc_end[2], possible_text))
                                        ali_words += anc_end[2] - anc_start[2] - anc_start[3]
                                else:
                                    # assign same possible text to each anc_segs
                                    start_seg_i = anc_start[2] + anc_start[3]
                                    for anc_seg in anc_segs:
                                        if start_seg_i == anc_seg[1]:
                                            start_seg_i = 0
                                            continue
                                        alignment.write("%s %d %d %d = %s\n" % 
                                            (asr_file_id, anc_seg[0], 
                                             start_seg_i, anc_seg[1], possible_text))
                                        ali_words += anc_seg[1] - start_seg_i
                                        start_seg_i = 0
                                    # if we have some unaligned start of seg, add it too
                                    if anc_end[2] != 0:
                                        alignment.write("%s %d %d %d = %s\n" % 
                                            (asr_file_id, anc_end[1], 0, anc_end[2], possible_text))
                                        ali_words += anc_end[2]
                            anc_start = (asr_file_id, seg, match_beg, match_len)
                            possible_text = []
                            anc_segs = []
                            anc_end = None
                        ali_words += match_len
                    match_len = 0
                    match_len_char = 0
                else:
                    if match_len != 0:
                        # match run continues
                        match_len += 1
                        match_len_char += len(ref[j])
                    else:
                        # first word in a match run
                        match_beg = seg_i
                        match_len = 1
                        match_len_char = len(ref[j])

                # move to next token
                if op == "M":
                    # add to possible text
                    possible_text.append(ref[j])
                    j += 1
                    i += 1
                    seg_i += 1
                elif op == "D":
                    # add to possible text
                    possible_text.append(ref[j])
                    j += 1
                elif op == "I":
                    seg_i += 1
                    i += 1
                elif op == "X":
                    # add to possible text
                    possible_text.append(ref[j])
                    seg_i += 1
                    j += 1
                    i += 1

                if sum([len(w) for w in possible_text]) > max_possible_phones:
                    # text is too long, discard anchor point
                    anc_start = None
                    possible_text = []
                    anc_segs = []
            else:
                i += 1
                seg_i += 1

        print "%d (%d%%) from %d words saved for force alignment" % (ali_words, 100*ali_words / float(len(asr)), len(asr))

def find_good_wordseq(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, asr_file_id, alignment):
        thresh = 11 * 2 # threshold in characters, 11 is average word length 

        i = 0
        seg = 0
        cigar_op = None
        cigar_i = 0
        j = ali_r_pos
        ali_words = 0

        match_beg = -1
        match_len = 0
        c_match_len = 0 # match len in characters
        seg_i = 0

        # NB: currently only cigar from ops with count=1 is supported
        while i < len(asr):
            if len(ali_cigar) < 2:
                break
            if asr[i] == "|" and ali_cigar[1] == 'Y':
                if c_match_len > thresh:
                    # found a match run with sufficient length
                    alignment.write("%s %d %d %d\n" % (asr_file_id, seg, match_beg, match_len))
                    ali_words += match_len
                # new segment started
                match_len = 0
                c_match_len = 0
                seg += 1
                seg_i = 0
                # skip ali op for delimeter 
                if i >= ali_q_pos:
                    ali_cigar = ali_cigar[2:]                    
                i += 1
            elif i >= ali_q_pos:
                # advance in cigar
                cigar_op = re.search("^1(\w)", ali_cigar)
                if cigar_op is None:
                    break
                op = cigar_op.group(1)
                # remove op from cigar
                ali_cigar = ali_cigar[cigar_op.end(1):]                
                
                # eval cigar op
                if op != "M":
                    if c_match_len > thresh:
                        # found a match run with sufficient length
                        alignment.write("%s %d %d %d\n" % (asr_file_id, seg, match_beg, match_len))
                        ali_words += match_len
                    match_len = 0
                    c_match_len = 0
                else:
                    if match_len != 0:
                        # match run continues
                        match_len += 1
                        c_match_len += len(ref[j])
                    else:
                        # first word in a match run
                        match_beg = seg_i
                        match_len = 1
                        c_match_len = len(ref[j])
                
                # move to next token
                if op == "M":
                    j += 1
                    i += 1
                    seg_i += 1
                elif op == "D":
                    j += 1
                elif op == "I":
                    seg_i += 1
                    i += 1
                elif op == "X":
                    seg_i += 1
                    j += 1
                    i += 1
            else:
                i += 1
                seg_i += 1

        print "%d (%d%%) from %d words aligned" % (ali_words, 100*ali_words / float(len(asr)), len(asr))

def find_good_segments(asr, ref, ali_q_pos, ali_r_pos, ali_cigar, asr_file_id, alignment):
        thresh = 0.15

        i = 0
        seg = 0
        match_score = 0
        transcript = []
        cigar_op = None
        cigar_seg = []
        cigar_i = 0
        j = ali_r_pos
        ali_seg = 0

        # NB: currently only cigar from ops with count=1 is supported
        while i < len(asr):
            if len(ali_cigar) < 2:
                break
            if asr[i] == "|" and ali_cigar[1] == 'Y':
                # normalize score
                if len(transcript) > 0:
                    match_score = float(match_score) / float(len(transcript))
                else:
                    match_score = 1
                if match_score <= thresh:
                    # save cigar segment and transcript
                    ali_seg += 1
                    alignment.write("%s %d\n" % (asr_file_id, seg))                
                seg += 1    
                match_score = 0
                # skip ali op for delimeter 
                if i >= ali_q_pos:
                    ali_cigar = ali_cigar[2:]
                transcript = []
                i += 1
            elif i >= ali_q_pos:
                cigar_op = re.search("^1(\w)", ali_cigar)
                if cigar_op is None:
                    break
                op = cigar_op.group(1)
                # remove op from cigar
                ali_cigar = ali_cigar[cigar_op.end(1):]
                # add to seg cigar
                cigar_seg.append((1, op))

                if op == "M":
                    # basically count the number of correctly recognized words
                    transcript.append(ref[j])
                    j += 1
                    i += 1
                elif op == "D":
                    match_score += 1
                    transcript.append(ref[j])
                    j += 1
                elif op == "I":
                    match_score += 1
                    i += 1
                elif op == "X":
                    match_score += 1
                    transcript.append(ref[j])
                    j += 1
                    i += 1
            else:
                i += 1

        if seg == 0:
            seg = 1 # prevent division by zero
        print "%d (%d%%) from %d segments aligned" % (ali_seg, 100*ali_seg / float(seg), seg)


def to_sec(hms):
    hms = hms.split(",")
    msec = float(hms[1]) / 1000
    hms = hms[0].split(":")
    sec = int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
    return float(sec + msec)

def create_corpus_seg():
    # load alignment
    ali = defaultdict(list)
    for line in open("alignment","r"):
        line = line.strip().split()
        ali[line[0][:-4]].append(int(line[1]))
    
    cname = None
    seg = 0
    corpus_size = 0
    textfile=open("crp1/text","w")
    utt2spk=open("crp1/utt2spk","w")
    wavscp=open("crp1/wav.scp","w")
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        name = decode_fname(fname)
        if cname != name:
            seg = 0
            cname = name
        srt = open("asr/%s.srt" % fname, "r")
        i = 1
        for l_srt in srt:
            if i % 4 == 2:
                # process timing
                # e.g. string like 00:00:00,030 --> 00:00:02,010
                begin, end = l_srt.strip().split("-->")
                begin = to_sec(begin)
                end = to_sec(end)
            if i % 4 == 3:                
                text = l_srt.strip()
                if seg in ali[cname]:
                    corpus_size += end - begin
                    words = text.split()
                    speaker = "spk%s%s" % (cname, words[0][:-1])
                    utt_id = "part-%s" % (seg)
                    words = words[1:]
                    # write corpus
                    textfile.write("%s-%s %s\n" % (speaker, utt_id, " ".join(words)))
                    utt2spk.write("%s %s\n" % (speaker, utt_id))
                    wavscp.write("%s-%s sox audio/%s -r 16k -t wav - trim %s %s |\n" % (speaker, utt_id, fname, begin, end-begin))
                seg += 1
            i += 1

    print "Created corpus of size: " + str(corpus_size)

def create_corpus_words():
    # load alignment
    ali = dict()
    for line in open("word_alignment","r"):
        line = line.strip().split()
        if line[0][:-4] not in ali:
            ali[line[0][:-4]] = defaultdict(list)
        ali[line[0][:-4]][int(line[1])].append([int(x) for x in line[2:]])

    cname = None
    seg = 0
    corpus_size = 0
    textfile=open("crp2/text","w")
    utt2spk=open("crp2/utt2spk","w")
    wavscp=open("crp2/wav.scp","w")
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        name = decode_fname(fname)
        if cname != name:
            seg = 0
            cname = name
        if not os.path.exists("asr/%s.srt" % fname):
            print "No srt file for %s. Skipping..." % fname
            continue
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
                    # loop through all alignments
                    lastword = 0
                    for (start, count) in ali[cname][seg]:
                        # get utterance id
                        utt_id = "part-%s-%s" % (seg, start)
                        words = text[1+start:1+start+count]
                        # read ctm timings                       
                        ctmline = ctm[ctm_i+start].strip().split()
                        tmp = ctmline[0]
                        begin = float(ctmline[2])
                        ctmline = ctm[ctm_i+start+count-1].strip().split()
                        if tmp != ctmline[0]:
                            print "CTM misalignment found!"
                            print cname, seg, start, count, ctmline                            
                        end = float(ctmline[2]) + float(ctmline[3])
                        # add segment offset
                        begin += parseCtmSegName(ctmline[0])
                        end += parseCtmSegName(ctmline[0])
                        # write corpus
                        corpus_size += end-begin
                        textfile.write("%s-%s %s\n" % (speaker, utt_id, " ".join(words)))
                        utt2spk.write("%s-%s %s\n" % (speaker, utt_id, speaker))
                        wavscp.write("%s-%s sox 'audio/%s' -r 16k -t wav - trim %s %s |\n" % (speaker, utt_id, fname, begin, end-begin))
                # -1 because first word is speaker_id (not included in ctm)
                ctm_i += len(text)-1
                seg += 1
            i += 1

    print "Created corpus of size: " + str(corpus_size)

def parseCtmSegName(segName):
    #S103-part_0000.030-0002.010
    parse = segName.split("_")[-1].split("-")
    return float(parse[0])
        
if len(sys.argv) == 2:
    try:
        stages = sys.argv[1].split(",")
    except:
        print "Incorrect stage list supplied. Should be a comma-separated list, like 1,2,3,4"
        stages = []
else:
    stages = ["1","2","3","4"]

if "1" in stages:
    start_file_align()

if "2" in stages:
    start_transcript_align()

if "3" in stages:
    create_corpus_seg()

if "4" in stages:
    create_corpus_words()
