#!/usr/bin/env python3
""" Module for handling device connectivity and workload execution along with power sampling

Author(s): 
 - Vaisakh P S <vaisakhp@iisc.ac.in>
Date: 29-10-2023

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
import socket
import csv
import datetime
import time
import threading
import select
import os


###############################################################################
# Utility class for processing UDP packet of power readings
###############################################################################
class SmartPower3_NCSampler:

    """
    Ref: https://wiki.odroid.com/accessory/power_supply_battery/smartpower3#logging_protocol
    """
    pd_col_info = [
                    'utctime',
                    'localtime',
                    'sm_mstime',
                    'ps_ippwr-volts_mV','ps_ippwr-ampere_mA','ps_ippwr-watt_mW','ps_ippwr-status_b',
                    'dev_ippwr-ch0-volts_mV', 'dev_ippwr-ch0-ampere_mA', 'dev_ippwr-ch0-watt_mW', 'dev_ippwr-ch0-status_b', 'dev_ippwr-ch0-interrupts',
                    'dev_ippwr-ch1-volts_mV', 'dev_ippwr-ch1-ampere_mA','dev_ippwr-ch1-watt_mW', 'dev_ippwr-ch1-status_b', 'dev_ippwr-ch1-interrupts',
                    'crc8-2sc', 'crc8-xor'
    ]
    
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0',6000))
        self.sock.setblocking(0)
        self.bExit = False
        self.f = None
        self.write = None
        self.sampling_thread = None
    

    def __ProcessPacket(self)-> None:
        """Function to process each packets, this will wait indefinitely until interrupted"""
        try:
            while (self.bExit == False):
                ready = select.select([self.sock], [], [], 1)
                if ready[0]:
                    data, _ = self.sock.recvfrom(81)
                    fields = data.strip().split(b',')
                    row = [datetime.datetime.utcnow()]+[datetime.datetime.now()]+fields
                    self.writer.writerow(row)
        except socket.timeout:
            print("\nerror: socket timeout")
    
    def StartSampling(self, filename:str)->None:
            self.bExit = False
            self.f = open(filename, "w", newline="")
            self.writer = csv.writer(self.f)
            self.writer.writerow(self.pd_col_info)

            self.sampling_thread = threading.Thread(target = self.__ProcessPacket)
            self.sampling_thread.start()

    def StopSampling(self,)->None:
        self.bExit = True
        self.sampling_thread.join()
        self.f.close()
        self.f = None
        self.writer = None


###############################################################################
# Utility class for Workload execution of device
###############################################################################
class WorkloadRecord:
    """Class to hold record of workload information
    
    Serves as just as wrapper for holding info
    """
    __name:str = ''
    __cmd:str = ''
    __options:str = ''

    def __init__(self, name:str , cmd:str, options:str) -> None:
        self.__name = name
        self.__cmd = cmd
        self.__options = options

    def name(self):
        return self.__name
    
    def val(self):
        return self.__name,self.__cmd,self.__options
    
    def cmd(self):
        return self.__cmd +' '+self.__options

    def __str__(self) -> str:
        return f'Workload: {self.__name} ## {self.__cmd} ## {self.__options}'
    

class Workloads:
    """Class to handle list of workloads"""
    
    # Perf Command options breakdown
    __perf_stat_cmd_prefix='sudo perf stat'
    __perf_stat_cmd_result_options='--summary -o '
    __perf_stat_cmd_sampling_options='-I 100 '
    __perf_stat_cmd_cpu_options='-a' 
    __perf_stat_cmd_repeat_options='-r ' 
    ## Perf events to be monitored.
    __perf_event_listing=\
            'branch-instructions,branch-misses,branch-load-misses,branch-loads,'\
            'bus-cycles,cpu-cycles,instructions,'\
            'cache-misses,cache-references,'\
            'cpu-clock,'\
            'context-switches,cpu-migrations,'\
            'L1-dcache-load-misses,L1-dcache-loads,L1-dcache-store-misses,L1-dcache-stores,'\
            'L1-icache-load-misses,L1-icache-loads,'\
            'LLC-load-misses,LLC-loads,LLC-store-misses,LLC-stores,'\
            'major-faults,minor-faults,page-faults,'\
            'dTLB-load-misses,dTLB-store-misses,iTLB-load-misses,'\
            'power:cpu_frequency,power:cpu_frequency_limits,'\
            'power:cpu_idle,power:cpu_idle_miss,'\
            'devfreq:devfreq_frequency,devfreq:devfreq_monitor,'\
            'power:clock_set_rate'

    def __init__(self, workloads:[WorkloadRecord], iterations:int) -> None:
        """Constructor, initialized with list of workloads"""
        self.__workload_count = len(workloads)
        self.__workloads = []
        self.__resultsfile = []
        for item in workloads:
            results_file = 'results/'+item.name()+'.prof'
            workload_cmd_temp = self.__perf_stat_cmd_prefix +' '\
                            + self.__perf_stat_cmd_result_options + results_file +' '\
                            + self.__perf_stat_cmd_sampling_options +' '\
                            + self.__perf_stat_cmd_cpu_options +' '\
                            + self.__perf_stat_cmd_repeat_options + str(iterations) +' '\
                            + '-e ' + self.__perf_event_listing +' '\
                            + item.cmd()
            self.__workloads.append(workload_cmd_temp)
            self.__resultsfile.append(results_file)


    def __len__(self):
        """Return length of workloads initialized

        Ref: https://www.geeksforgeeks.org/python-__len__-magic-method/
        """
        return self.__workload_count
    

    def __iter__ (self):
        """To support iteration of workload list """
        self.__itr_ctr = 0
        return self
    
    def __next__(self):
        """Iterate through the workload list elements"""
        if self.__itr_ctr < self.__len__():
            x = str(self.__workloads[self.__itr_ctr])
            name = self.__resultsfile[self.__itr_ctr]
            self.__itr_ctr += 1
            return (name, x)
        else:
            raise StopIteration

    def dump (self):
        for item in self.__workloads:
            print (item)
    
    def results_files(self) -> [str]:
        return self.__resultsfile

class WorkloadManager:
    """Class to handle workloads and execute them on target device

    Right now transport medium will be ssh, later will integrate UART/TTY
    support too. 
    """
    def __init__(self, 
                 dev_ipaddr:str,
                 dev_user:str,
                 dev_pass:str,
                 workloads:Workloads) -> None:
        self.__workloads = workloads
        self.__dev_ipaddr = dev_ipaddr
        self.__dev_user = dev_user
        self.__dev_pass = dev_pass

        self.__ssh_fabric_con = fabric.Connection(self.__dev_ipaddr, 
                                    port=22,                ## SSH Port
                                    user=self.__dev_user,   ## Username 
                                    connect_kwargs={        
                                        'password':self.__dev_pass  ## Password
                                    })
        
        self.__powerMonSampler = SmartPower3_NCSampler()
        
    
    def batch_execute(self) -> None:
        """Sequentially Execute the workloads"""

        ## Create results directory
        self.__ssh_fabric_con.run ('mkdir -p results')

        ## Iterate and execute each jobs
        for workload_item in self.__workloads:
            result = workload_item[0]
            cmd = workload_item[1]

            ## Start sampling via SmartPower3
            self.__powerMonSampler.StartSampling(result+'.powdata')

            ## Execute the workload on device
            self.__ssh_fabric_con.run(cmd)

            ## Stop power data sampling from SmartPower3
            self.__powerMonSampler.StopSampling()

            ## Fetch results from remote
            self.__ssh_fabric_con.get(result,'results/'+os.path.basename(result))


if __name__ == '__main__':

    results_dirname = 'results'
    parent_dirname = os.curdir
    results_path = os.path.join(parent_dirname,results_dirname)
    if (os.path.exists(results_path) == False):
        os.mkdir(results_path)

    workload_listing = []
    ## List out the workloads
    workload_listing.append(WorkloadRecord('stress-1cpu-10s',
                        'stress','-c 1 -t 10s'))
    workload_listing.append(WorkloadRecord('stress-2cpu-10s',
                        'stress','-c 2 -t 10s'))
    workload_listing.append(WorkloadRecord('stress-3cpu-10s',
                        'stress','-c 3 -t 10s'))
    workload_listing.append(WorkloadRecord('stress-4cpu-10s',
                        'stress','-c 4 -t 10s'))
    workloads_obj = Workloads(workload_listing, 1)
    
    workloads = WorkloadManager(dev_ipaddr='192.168.0.101',
                        dev_user = 'root',
                        dev_pass = 'odroid',
                        workloads = workloads_obj
                        )
    workloads.batch_execute()
    

