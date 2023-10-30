#!/usr/bin/env python3
""" Module for handling device connectivity and workload execution

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
    __perf_stat_cmd_repeat_options='-r 10' 
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

    def __init__(self, workloads:[WorkloadRecord]) -> None:
        """Constructor, initialized with list of workloads"""
        self.__workload_count = len(workloads)
        self.__workloads = []
        self.__resultsfile = []
        for item in workloads:
            results_file = item.name()+'.prof'
            workload_cmd_temp = self.__perf_stat_cmd_prefix +' '\
                            + self.__perf_stat_cmd_result_options + item.name()+'.prof'+' '\
                            + self.__perf_stat_cmd_sampling_options +' '\
                            + self.__perf_stat_cmd_cpu_options +' '\
                            + self.__perf_stat_cmd_repeat_options + ' '\
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
            self.__itr_ctr += 1
            return x
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
        
        # self.__workloads.dump()
    
    def batch_execute(self) -> None:
        """Sequentially Execute the workloads"""
        for workload_item in self.__workloads:
            self.__ssh_fabric_con.run(workload_item)
            # print (workload_item)
    
    def download_results(self) -> None:
        """ Pull results file of workload from device"""
        result_files = self.__workloads.results_files()
        for results_file in result_files:
            self.__ssh_fabric_con.get(results_file,'')


if __name__ == '__main__':
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
    
    # for i in workload_listing:
    #     print(i)
    workloads_obj = Workloads(workload_listing)

    workloads = WorkloadManager(dev_ipaddr='192.168.0.101',
                        dev_user = 'root',
                        dev_pass = 'odroid',
                        workloads = workloads_obj
                        )
    # workloads.batch_execute()
    workloads.download_results()
    

