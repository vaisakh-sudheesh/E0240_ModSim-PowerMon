#!/usr/bin/env python3
""" Module for handling device connectivity and workload execution along with power sampling

Author(s): 
 - Vaisakh P S <vaisakhp@iisc.ac.in>
Date: 10-11-2023

Assumptions:
  N/A

Limitations:
  N/A

Warnings:
  N/A

TODO:
  N/A
"""

import fabric
import tarfile
import sys
import os
import shutil

from pathlib import Path
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))
from src import workloads as work

## ----------------------------------------------------------------------------
src_root = Path(__file__).parents[0]
print(src_root)

idle_bigcore_freq_list = [2000000, 1900000, 1800000, 1700000, 1600000, 1500000, 1400000, 1300000 , 1200000 ]
idle_littlecore_freq_list = [1400000, 1300000 , 1200000, 1100000, 1000000, 900000, 800000 ]

workload_data_dir = os.path.join(src_root,'data')
workload_result_dir = os.path.join(src_root,'results')
conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:bz2") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def execute_workload (test_desc_prefix:str, on_bigcluster:bool=True, freq_list:[int]=bigcore_freq_list ):
    for freq in freq_list:
        test_desc_composed=test_desc_prefix+'-CPUFreq-'+str(freq/1000000)+'GHz'
        # Setup the workload
        cpuload_wkld = work.CPUIntensiveWorkloads(conn,
                                run_on_bigcore=on_bigcluster,
                                iteration_count=5,
                                enable_stress_workloads= True,
                                enable_compress_workloads = True,
                                enable_encode_workloads = True 
                          )
        cpuload_wkld.setup_persistant(workload_data=workload_data_dir, resultsdir_prefix=workload_result_dir, testname_suffix=test_desc_composed)
        # Run the workload
        results = cpuload_wkld.run(cpu_freq=freq )
        # Tar the results folder and move the directory to backup rather than deleting it
        make_tarfile(os.path.join(workload_result_dir, os.path.basename(results)+'.tar.bz2'),results)
        shutil.move(results, workload_result_dir+'/backup/')
        del cpuload_wkld


def execute_idle_scenario (test_desc_prefix:str, on_bigcluster:bool=True, freq_list:[int]=bigcore_freq_list ):
    for freq in freq_list:
        test_desc_composed=test_desc_prefix+'-CPUFreq-'+str(freq/1000000)+'GHz'
        # Setup the workload
        idle_wkld = work.IdleWorkloads(conn,
                                run_on_bigcore=on_bigcluster,
                                idle_duration=60,
                          )
        idle_wkld.setup_persistant(resultsdir_prefix=workload_result_dir, testname_suffix=test_desc_composed)
        # Run the workload
        results = idle_wkld.run(cpu_freq=freq )
        # Tar the results folder and move the directory to backup rather than deleting it
        make_tarfile(os.path.join(workload_result_dir, os.path.basename(results)+'.tar.bz2'),results)
        shutil.move(results, workload_result_dir+'/backup/')
        del idle_wkld

if __name__ == '__main__':

    execute_idle_scenario (test_desc_prefix='Idleworkload-LittleCore-60sidle', on_bigcluster=False, freq_list= idle_littlecore_freq_list)
    execute_idle_scenario (test_desc_prefix='Idleworkload-BigCore-60sidle', on_bigcluster=True, freq_list= idle_bigcore_freq_list)

