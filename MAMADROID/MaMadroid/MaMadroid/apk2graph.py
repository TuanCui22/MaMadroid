# apk2graph.py
import os
import networkx as nx
from androguard.misc import AnalyzeAPK

def extractcg(apkpath, gmlpath):
    """
    Extracts the call graph from an APK and saves it as a GML file.

    Parameters:
        apkpath (str): Path to the APK file.
        gmlpath (str): Path to save the GML file.
    """
    try:
        a, d, dx = AnalyzeAPK(apkpath)
        
        # Create a directed graph
        cg = nx.DiGraph()

        # Populate the graph with methods and their calls
        for method in dx.get_methods():
            method_node = f"{method.class_name}->{method.name}{method.descriptor}"
            cg.add_node(method_node)
            for _, callee, _ in method.get_xref_to():
                callee_node = f"{callee.class_name}->{callee.name}{callee.descriptor}"
                cg.add_edge(method_node, callee_node)

        # Write the graph to a GML file
        nx.write_gml(cg, gmlpath)
        
        # Validate the GML file
        with open(gmlpath, 'r') as gml_file:
            content = gml_file.read().strip()
            if not content or len(content) < 10:  # Adjust threshold as needed
                raise ValueError("GML file is empty or too short, something went wrong during writing")

    except Exception as e:
        print(f"Error generating GML for {apkpath}: {e}")
        if os.path.exists(gmlpath):
            os.remove(gmlpath)
        raise