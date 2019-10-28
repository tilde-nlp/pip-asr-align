#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import argparse
import subprocess
import os

class G2PConverter:
    phone_to_graph_map = {"A":"a", "AA":"ā", "B":"b", "C":"c", "CH":"č", "D":"d", "E":"e", "EE":"ē", "F":"f", "G":"g", "GJ":"ģ", "H":"h", "I":"i", "II":"ī", "J":"j", "K":"k", "KJ":"ķ", "L":"l", "LJ":"ļ", "M":"m", "N":"n", "NJ":"ņ", "O":"o", "P":"p", "R":"r", "S":"s", "SH":"š", "T":"t", "U":"u", "UU":"ū", "V":"v", "Z":"z", "ZH":"ž", "IE":"ie","AI":"ai"}

    letters = set(u'aābcčdeēfgģhiījkķlļmnņoóōprsštuūvzž' + u'xwqy' + u'EĒ')
    transform = {
            u'ā': 'aa',
            u'ē': 'ee',
            u'ī': 'ii',
            u'ū': 'uu',
            u'č': 'ch',
            u'š': 'sh',
            u'ž': 'zh',
            u'ģ': 'gj',
            u'ķ': 'kj',
            u'ļ': 'lj',
            u'ņ': 'nj',
            u'x': 'k s',
            u'q':'k',
            u'y':'i',
            u'w': 'v',
            }

    def __init__(self, args):
        self.excp_list = list()
        self.excp_pron = list()
        self.prondict = dict()
        self.dir = os.path.dirname(os.path.realpath(__file__))
    
    def phoneme_to_grapheme(self,phones):
        phone_list = phones.split()
        result = list()
        for phone in phone_list:
            result.append(self.phone_to_graph_map[phone])
        return result
    
    def loadExceptions(self,excp_file):
        self.excp_list = [tmp.decode('utf-8').rstrip("\n").split("\t")[0] for tmp in open(excp_file,"r").readlines()]
        self.excp_pron = [" ".join(tmp.decode('utf-8').rstrip("\n").split("\t")[1:]) for tmp in open(excp_file,"r").readlines()]
         
    def isInExcpList(self,token):
        if token in self.excp_list:
            return True
        else:
            return False
    
    def convertExcpFromList(self,excp):
            if excp in self.excp_list:
                return self.excp_pron[self.excp_list.index(excp)]
            else:
                return self.excp_pron[self.excp_list.index(excp.replace("+",""))]
            
    def load_phondict(self, path):
        for line in codecs.open(path, 'r', 'utf-8'):
            line = line.rstrip().split()
            if len(line) == 2:
                (graph, phon) = line
                self.prondict[graph] = list(phon)
            else:
                self.prondict[line[0]] = line[1:]

    def transform_upper(self, graphemes):
        for c in graphemes:
            yield c.upper()

    def transform_simple(self, graphemes):
        graphemes = list(graphemes)
        last_i = len(graphemes) - 1
        i = -1
        for c in graphemes:
            i += 1
            if not c in self.letters:
                continue
            if c in self.transform:
                yield self.transform[c]
                continue
            yield c

    def convert(self, graphemes):
        if graphemes and graphemes[0] == '<':
            return ['++' + graphemes[1:-1].upper() + '++']
        if graphemes in self.prondict:
            return self.prondict[graphemes]
        result = graphemes.lower()
        result = self.transform_simple(result)
        result = self.transform_upper(result)
        result = list(result)
        if result[0] == "SL_SIL":
            result = result[1:]
        if result[-1] == "SL_SIL":
            result = result[:-1]
        return result

