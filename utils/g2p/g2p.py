#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import argparse
import subprocess
import os
            
parser = argparse.ArgumentParser(description='Grapheme-to-phoneme converter')
parser.add_argument('-d', '--dict', help='load pronunciation dictionary')
parser.add_argument('-e', '--excpt', help='include exception file with words, that are pronounced specially. will be print in the beggining')

parser.add_argument('lang', metavar="lang", nargs='?', help='G2P input language', default = "lv")
args = parser.parse_args()

if args.lang == "lv":
    from g2p_lv import G2PConverter
elif args.lang == "lt":
    from g2p_lt import G2PConverterLT as G2PConverter
else:
    raise NotImplementedError("language not implemented: %s" % args.lang)

g2p = G2PConverter(args)

if args.dict:
    g2p.load_phondict(args.dict)

if args.excpt:
    g2p.loadExceptions(args.excpt)

filein = sys.stdin
rx_ws = re.compile(r'\s+')

ln = 0
for line in filein:
    try:
        ln += 1
        line = line.decode('utf-8').rstrip()
        transcript = line
        tokens = rx_ws.split(transcript)
        if not tokens:
            continue
        graphemes = list()
        for t in tokens[:1]:
            if args.excpt:
                if g2p.isInExcpList(t):
                    pron = g2p.convertExcpFromList(t).split(" ")
                    for p in pron:
                        print ("%s %s" % (t," ".join(g2p.convert(p)))).encode('utf-8')
                else:
                    # not an exception
                    out = " ".join(g2p.convert(t))
                    if out:
                        print ("%s %s" % (t,out)).encode('utf-8')
            else:
                # simple case
                print ("%s %s" % (t," ".join(g2p.convert(t)))).encode('utf-8')
    except:
        print("Error in line %s. Skipping..." % ln)
