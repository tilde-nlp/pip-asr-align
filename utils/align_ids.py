import os
import pickle
from collections import defaultdict

def start_file_align():
    asr_files = list(os.walk("parts"))[0][2]
    asr_files = sorted([x for x in asr_files])
    ref_files = list(os.walk("ref"))[0][2]
    ref_files = sorted([x for x in ref_files])
    alignment = defaultdict(list)
    for asr_file in asr_files:
        for ref_file in ref_files:
            ref_name = ref_file.replace("_","").split(".")
            ref_name = ".".join(ref_name[:-1]) if len(ref_name)>1 else ref_name[0]
            asr_name = asr_file.replace("_","").split(".")
            asr_name = ".".join(asr_name[:-1]) if len(asr_name)>1 else asr_name[0]
            if ref_name == asr_name:
            	# map
            	alignment[ref_file].append(asr_file)
            	# go to next ref
    # save alignment
    pickle.dump(alignment, open("file_alignment", "w"))

def decode_fname(fname):    
    fname = fname.split(".")
    return ".".join(fname[:-1]) if len(fname)>1 else fname[0]
