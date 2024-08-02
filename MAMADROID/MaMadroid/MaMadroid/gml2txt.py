# coding=utf-8

import os
import igraph
from collections import defaultdict
from parse import parse_label

def caller2callee(edgelist, nodes, filename):
    """
    Converts the call graph information from the GML file into a text file.

    Parameters:
        edgelist (list): List of tuples representing edges in the call graph.
        nodes (list): List of nodes in the call graph.
        filename (str): The path to store the output text file.
    """
    edges = defaultdict(list)
    edgesname = defaultdict(list)
    
    for k, v in edgelist:
        edges[k].append(v)
        edgesname[parse_label(nodes[k]["label"])].append(parse_label(nodes[v]["label"]))
    
    with open(filename, 'w') as out:
        for node, callees in edgesname.items():
            # Concatenate the caller and callees into a single string
            call = f"{node} ==> {' '.join(callees)}"
            out.write(call + "\n")

def gml2graph(gmlpath):
    """
    Reads the GML file to retrieve all nodes and edge information from the call graph.

    Parameters:
        gmlpath (str): The path to the GML file.

    Returns:
        tuple: A tuple containing the graph object and the list of edge tuples.
    """
    try:
        g = igraph.Graph.Read_GML(gmlpath)
        edgelist = g.get_edgelist()
        return g, edgelist
    except Exception as e:
        print(f"Error reading GML file {gmlpath}: {e}")
        raise
