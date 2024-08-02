# coding=utf-8
"""
info: Read abstracted txt files obtained from different modes and convert them into Markov matrices.
"""
import numpy
import sys


# Dummy Coding for Markov Transition matrix
def dummy_coding(imported, allnodes, wf):
    """
    Dummy coding function.
    """
    DCVector = []
    for i in range(len(imported)):
        DCVector.append([])
        if wf == 'Y':
            callsline = imported[i].split('\t')
        else:
            callsline = imported[i]
        for v in range(len(callsline)):
            for s in range(len(allnodes)):
                if callsline[v] == allnodes[s]:
                    DCVector[i].append(s)
    return DCVector


# This function creates the output matrix that shows all the transition probabilities from one state to the other.
def matrix_creation(DCVector, allnodes):
    """
    Create the output matrix showing transition probabilities.
    """
    s = (len(allnodes), len(allnodes))
    MarkovTransition = numpy.zeros(s)
    MarkovFeats = numpy.zeros(s)

    for s in range(len(DCVector)):
        for i in range(1, len(DCVector[s])):
            MarkovTransition[DCVector[s][0], DCVector[s][i]] += 1

    for i in range(len(MarkovTransition)):
        Norma = numpy.sum(MarkovTransition[i])
        if Norma == 0:
            MarkovFeats[i] = MarkovTransition[i]
        else:
            MarkovFeats[i] = MarkovTransition[i] / Norma

    return MarkovFeats


def main(imported, alln, wf):
    """
    Main function.
    """
    DCV = dummy_coding(imported, alln, wf)
    MarkovFeatures = matrix_creation(DCV, alln)
    return MarkovFeatures
