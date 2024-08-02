# mamadroid.py

import os
import time
import argparse
import logging
from abstractGraph import _preprocess_graph
from apk2graph import extractcg
from gml2txt import caller2callee, gml2graph
from markov_processor import process_files

def setup_logging(output):
    logfile = os.path.join(output, 'MaMadroid/log.txt')
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    return logfile

def process_apk_to_gml(apkfile, gmlfile):
    for filename in os.listdir(apkfile):
        if filename.endswith(".apk"):
            try:
                gmlpath = os.path.join(gmlfile, filename.rpartition(".")[0] + ".gml")
                filenames = os.path.join(apkfile, filename)
                extractcg(filenames, gmlpath)
            except Exception as e:
                logging.error(f"Error processing {filename} to gml: {e}")
            else:
                logging.info(f"{filename} to gml done")

def process_gml_to_txt(gmlfile, txtfile):
    for gmlname in os.listdir(gmlfile):
        try:
            storepath = os.path.join(txtfile, gmlname.rpartition(".")[0] + ".txt")
            gmlnames = os.path.join(gmlfile, gmlname)
            g, edgelist = gml2graph(gmlnames)
            caller2callee(edgelist, g.vs, storepath)
        except Exception as e:
            logging.error(f"Error processing {gmlname} to txt: {e}")
        else:
            logging.info(f"{gmlname} to txt done")

def abstract_graphs(txtfile, app_dir, log):
    num = 0
    for txtname in os.listdir(txtfile):
        try:
            txtpath = os.path.join(txtfile, txtname)
            _preprocess_graph(txtpath, app_dir)
            logging.info(f"{txtname.rpartition('.')[0]}.apk is abstracted")
            num += 1
        except Exception as e:
            logging.error(f"Error processing {txtname}: {e}")
            log.write(f"Error processing {txtname}: {e}\n")
    log.write(f"{num} APKs processed.\n")

def process_markov_matrices(directory, output_path, type_, file_list, logfile):
    process_files(directory, output_path, type_, file_list, logfile=logfile)

def mamadroid_main(apk, output, memory):
    gmlfile = os.path.join(output, 'MaMadroid/gml')
    txtfile = os.path.join(output, 'MaMadroid/graphs', 'Trial1')
    os.makedirs(gmlfile, exist_ok=True)
    os.makedirs(txtfile, exist_ok=True)

    logfile = setup_logging(output)

    process_apk_to_gml(apk, gmlfile)
    process_gml_to_txt(gmlfile, txtfile)

    with open(logfile, 'a') as log:
        app_dir = os.path.normpath(r'C:\Users\thanh\Downloads\MAMADROID\MaMadroid\MaMadroid')
        abstract_graphs(txtfile, app_dir, log)

    output_path = os.path.join(output, 'MaMadroid' ,'Features')
    family_output_path = os.path.join(output_path, 'Families')
    package_output_path = os.path.join(output_path, 'Packages')
    os.makedirs(family_output_path, exist_ok=True)
    os.makedirs(package_output_path, exist_ok=True)

    family_directory = r'C:\Users\thanh\Downloads\MAMADROID\MaMadroid\MaMadroid\family'
    family_file_list = r'C:\Users\thanh\Downloads\MAMADROID\MaMadroid\MaMadroid\Families11.txt'
    process_markov_matrices(family_directory, output_path, "Families", family_file_list, logfile)

    package_directory = r'C:\Users\thanh\Downloads\MAMADROID\MaMadroid\MaMadroid\package'
    package_file_list = r'C:\Users\thanh\Downloads\MAMADROID\MaMadroid\MaMadroid\Packages.txt'
    process_markov_matrices(package_directory, output_path, "Packages", package_file_list, logfile)

    logging.info("All processing steps completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MaMaDroid on a set of APK files.')
    parser.add_argument('-f', '--file', required=True, help='Path to the directory containing APK files.')
    parser.add_argument('-d', '--dir', required=True, help='Path to the output directory.')
    parser.add_argument('-m', '--memory', default='2G', help='Amount of memory allocated to the JVM heap space (e.g., 2G for 2 GB).')

    args = parser.parse_args()

    # Set JVM heap size
    os.environ['JAVA_TOOL_OPTIONS'] = f'-Xmx{args.memory}'

    time_start = time.time()
    try:
        mamadroid_main(args.file, args.dir, args.memory)
    except Exception as e:
        logging.error(f"An exception occurred while running Mamadroid: {e}")
    time_end = time.time()
    logging.info(f"Total time cost: {time_end - time_start} s")
