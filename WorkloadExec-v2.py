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
# For now just sticking to performance governor, not schedutil governor
bigcore_freq_list = [2000000, 1900000, 1800000, 1700000, 1600000, 1500000, 1400000, 1300000 , 1200000 ]

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:bz2") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

# if __name__ == '__main__':
#     test_desc_prefix='BigCore-10itr-50msSmplg'
#     for freq in bigcore_freq_list:
#         test_desc_composed=test_desc_prefix+'-CPUFreq-'+str(freq/1000000)+'GHz'
#         Run_Workload(test_desc_composed, cpu_freq=freq, iteration_count=5,
#                      enable_stress_workloads= True,
#                      enable_compress_workloads = True,
#                      enable_encode_workloads = True )
        
if __name__ == '__main__':
    src_root = Path(__file__).parents[0]
    print(src_root)
    workload_data_dir = os.path.join(src_root,'data')
    workload_result_dir = os.path.join(src_root,'results')

    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    test_desc_prefix='BigCore-10itr-100msPerf'
    for freq in bigcore_freq_list:
        test_desc_composed=test_desc_prefix+'-CPUFreq-'+str(freq/1000000)+'GHz'
        # Setup the workload
        cpuload_wkld = work.CPUIntensiveWorkloads(conn)
        cpuload_wkld.setup_persistant(workload_data=workload_data_dir, resultsdir_prefix=workload_result_dir, testname_suffix=test_desc_composed)
        # Run the workload
        results = cpuload_wkld.run(cpu_freq=freq )

        # Tar the results folder and move the directory to backup rather than deleting it
        make_tarfile(os.path.join(workload_result_dir, os.path.basename(results)+'.tar.bz2'),results)
        shutil.move(results, workload_result_dir+'/backup/')
        del cpuload_wkld
