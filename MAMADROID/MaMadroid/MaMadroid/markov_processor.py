# markov_processor.py

import os
import numpy as np
from time import time
from Markov import main

def process_files(directory, output_path, which_class, filename_list, logfile=None, wf='Y'):
    packets = []
    with open(filename_list) as file:
        packets = [line.strip() for line in file]

    allnodes = packets + ['self-defined', 'obfuscated']

    header = ['filename']
    for i in range(len(allnodes)):
        for j in range(len(allnodes)):
            header.append(allnodes[i] + 'To' + allnodes[j])

    database_res = [header]
    num_apps = os.listdir(directory)
    print(f"Processing {len(num_apps)} apps...")

    for index, app in enumerate(num_apps):
        print(f'Starting {index + 1} of {len(num_apps)}')
        with open(os.path.join(directory, app)) as file:
            specific_app = [line.strip() for line in file]

        start_time = time()
        mark_mat = main(specific_app, allnodes, wf)
        print(f"Dimensions of mark_mat: {len(mark_mat)}, {len(mark_mat[0])}")
        print(f"Expected dimensions: {len(allnodes)}, {len(allnodes)}")


        mark_row = [app] + [item for sublist in mark_mat for item in sublist]
        database_res.append(mark_row)
        print(f'Finished {app} in {time() - start_time} seconds.')

    with open(os.path.join(output_path, which_class, 'result.csv'), 'w') as file:
        for line in database_res:
            file.write(','.join(str(item) for item in line) + '\n')

    print(f"Data saved to {os.path.join(output_path, which_class, 'result.csv')}")

    # If logfile is provided, read it
    if logfile:
        with open(logfile, 'r') as log:
            print(log.read())  # Print the content of the log file
