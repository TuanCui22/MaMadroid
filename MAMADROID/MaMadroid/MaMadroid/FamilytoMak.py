#coding=utf-8
'''
info: Use Families11.txt as a list to call Markov.py to convert the files in the family folder to Markov matrices and store them in the Features/Families folder.
'''
import os
import numpy as np
from time import time
import Markov as mk

PACKETS = []

WHICHCLASS = "Families"

wf = "Y"
appslist = None
dbs = None

with open("Families11.txt", 'r', encoding='utf-8') as packseq:
    for line in packseq:
        PACKETS.append(line.strip())

allnodes = PACKETS
allnodes.append('self-defined')
allnodes.append('obfuscated')
print("allnodes:", allnodes, "\n")

Header = ['filename']
for i in range(len(allnodes)):
    for j in range(len(allnodes)):
        Header.append(allnodes[i] + 'To' + allnodes[j])
print('Header is long', len(Header))

Fintime = []
dbcounter = 0

numApps = os.listdir('family/')

DatabaseRes = [Header]

leng = len(numApps)
for i in range(leng):
    print('starting', i + 1, 'of', leng)
    if wf == 'Y':
        with open('family/' + str(numApps[i]), 'r', encoding='utf-8') as callseq:  # Families/Trail1
            specificapp = [line.strip() for line in callseq]
    else:
        specificapp = [line for line in dbs[dbcounter][i]]

    Startime = time()
    MarkMat = mk.main(specificapp, allnodes, wf)

    MarkRow = [numApps[i]] if wf == 'Y' else [appslist[dbcounter][i]]
    for i in range(len(MarkMat)):
        for j in range(len(MarkMat)):
            MarkRow.append(MarkMat[i][j])

    DatabaseRes.append(MarkRow)
    Fintime.append(time() - Startime)
dbcounter += 1

with open('Features/' + WHICHCLASS + '/' + "result.csv", 'w', encoding='utf-8') as f:
    for line in DatabaseRes:
        f.write(','.join(map(str, line)) + '\n')
