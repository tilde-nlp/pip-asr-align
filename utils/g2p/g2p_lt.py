#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import argparse
import subprocess
import os
from g2p_lv import G2PConverter

class G2PConverterLT(G2PConverter):
	phone_to_graph_map = {"A":"a", "AA":"ā", "B":"b", "C":"c", "CH":"č", "D":"d", "E":"e", "EE":"ē", "F":"f", "G":"g", "GJ":"ģ", "H":"h", "I":"i", "II":"ī", "J":"j", "K":"k", "KJ":"ķ", "L":"l", "LJ":"ļ", "M":"m", "N":"n", "NJ":"ņ", "O":"o", "P":"p", "R":"r", "S":"s", "SH":"š", "T":"t", "U":"u", "UU":"ū", "V":"v", "Z":"z", "ZH":"ž", "IE":"ie","AI":"ai"}

	letters = set(u'aąbcčdeęėfghiįyjklmnoprsštuųūvzž' + u'xwq')
	transform = {		
			u'ą': 'a',
			u'ę': 'ae',
			u'ė': 'ee',						
			u'į': 'ii',
			u'ū': 'uu',
			u'č': 'ch',
			u'š': 'sh',
			u'ž': 'zh',
			u'ų': 'uu',
			u'x': 'k s',
                        u'ņ': 'n j',
			u'q':'k',
			u'y':'ii',
			u'w': 'v',
			}
