import os
import sys
import re
from align_ids import decode_fname


def download_srt_ctm():
    for line in open("id.lst", "r"):
        line = line.strip().split()
        jobid = line[1][1:-2]
        fname = line[0]
        os.system("wget -O 'asr/%s' http://runa.tilde.lv/client/jobs/%s.ctm" % (fname+".ctm", jobid))
        os.system("wget -O 'asr/%s' http://runa.tilde.lv/client/jobs/%s.transcribed.srt" % (fname+".srt", jobid))

def toHMS(tm):
    tm = tm.split(".")
    seconds = int(tm[0])
    msec = int(tm[1])
    hours = seconds / 3600
    minutes = seconds / 60
    seconds = seconds % 60
    return "%02d:%02d:%02d,%03d" % (hours,minutes,seconds,msec)

def split_by_seg():
    if not os.path.exists("parts"):
        os.mkdir("parts")
    i = 0
    alltext=""
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        prev_segid=""
        srt = open("asr/%s.srt" % fname, "r")
        for rawctmline in open("asr/%s.ctm" % fname, "r"):
            ctmline=rawctmline.strip().split()
            segid=ctmline[0]
            time = segid.split("part_")[1].split("-")  
            time_start = time[0]
            time_end = time[1]   
            if prev_segid != segid:
                prev_segid = segid
                os.system('sox "tmpsplit/%s" "parts/part_%s.mp3" trim %s =%s'  % (fname, 
                                                                       i, time_start, time_end))
                # read text from SRT
                srt.readline() # number
                srt.readline() # time
                text = srt.readline().decode("utf-8")
                srt.readline() # delim
                
                time_end = float(time_end) - float(time_start)
                time_start = 0.0

                # write new ctm and srt
                octm = open("parts/part_%s.ctm" % i,"w")
                newsegid = segid.split("part_")[0] + "part_" + str(time_start) + "-" + str(time_end)
                ctmline[0] = newsegid
                octm.write(" ".join(ctmline))
                octm.write("\n")

                osrt = open("parts/part_%s.srt" % i, "w")
                osrt.write("1\n")
                osrt.write("%s --> %s\n" % (toHMS(str(time_start)), toHMS(str(time_end))))
                osrt.write("%s\n" % text.encode("utf-8"))

                alisegid = fname + "___" + str(i)

                alltext += alisegid.strip() + " " + txt_frm(text) + " "
                
                i += 1
            else: 
                ctmline[0] = newsegid
                octm.write(" ".join(ctmline))
                octm.write("\n")

    alltxtfile = open("parts/all.txt", "w")
    alltxtfile.write(alltext.encode("utf-8"))
    alltxtfile.close()

def glue_text():
    # get the sorted list "2*" files in directory "text" 
    files = list(os.walk("text"))[0][2]
    files = sorted([x for x in files if x[0] == "2"])
    # aa
    cmonth = None
    output = None
    for file_x in files:
        month = file_x[:6]
        if month != cmonth:
            if output:
                output.close()
            output = open("text/M_"+month,"w")
            delim = ""
            cmonth=month
        for line in open("text/"+file_x, "r"):
            output.write(delim + line.strip())
            delim = " "
    output.close()

def txt_frm(text):
    return text.strip().replace(".","").replace(",","").lower()

def glue_asr():
    if not os.path.exists("parts"):
        os.mkdir("parts")

    cmonth = None
    sink = None
    for line in open("id.lst", "r"):
        line = line.strip().split()
        fname = line[0]
        month = decode_fname(fname)
        if cmonth != month:
            # close old sink
            if sink:
                sink.close()
            # open new sink
            sink = open("parts/%s.txt" % month, "w")
            delim=""
            cmonth = month
        srt = open("asr/%s.srt" % fname, "r")
        i = 1
        for l_srt in srt:
            if i % 4 == 3:
                sink.write(delim)
                l_srt = " ".join(l_srt.strip().split()[1:]) # skip speaker id
                sink.write(l_srt)
                sink.write(" |")
                delim = " "
            i += 1

    sink.close()

if len(sys.argv) == 2:
    try:
        stages = sys.argv[1].split(",")
    except:
        print "Incorrect stage list supplied. Should be a comma-separated list, like 1,2,3,4"
        stages = []
else:
    stages = ["1","2","3"]

if "1" in stages:
    download_srt_ctm()

if "2" in stages:
#    split_by_seg()
    glue_asr()
    pass

if "3" in stages:
    glue_text()
    pass

    

