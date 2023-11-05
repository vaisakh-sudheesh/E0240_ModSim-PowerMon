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
        ## Time fields - UTC, Local and Milliseconds logged by SmartPower3
        'utctime','localtime','sm_mstime',
        ## Input Power parameters of SmartPower's power supply
        'ps_ippwr-volts_mV','ps_ippwr-ampere_mA','ps_ippwr-watt_mW','ps_ippwr-status_b',
        ## Channel-0's output supply parameters and status
        'dev_ippwr-ch0-volts_mV', 'dev_ippwr-ch0-ampere_mA', 'dev_ippwr-ch0-watt_mW', 
        'dev_ippwr-ch0-status_b', 'dev_ippwr-ch0-interrupts',
        ## Channel-1's output supply parameters and status
        'dev_ippwr-ch1-volts_mV', 'dev_ippwr-ch1-ampere_mA','dev_ippwr-ch1-watt_mW', 
        'dev_ippwr-ch1-status_b', 'dev_ippwr-ch1-interrupts',
        ## Checksum fields
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
        """Function to process each packets"""
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
    __perf_stat_cmd_sampling_options='-I 50 '
    __perf_stat_cmd_cpu_options='-a' 
    __perf_stat_cmd_repeat_options='-r ' 
    __task_cmd_prefix='taskset '
    __task_cmd_option_bigcores=' -c 4-7 '
    __task_cmd_option_littlecores=' -c 0-3 '

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
            'power:power_domain_target,power:powernv_throttle,'\
            'thermal:cdev_update,thermal:thermal_power_cpu_get_power_simple,'\
            'thermal:thermal_power_cpu_limit,thermal:thermal_temperature,'\
            'thermal:thermal_zone_trip,thermal_pressure:thermal_pressure_update,'\
            'devfreq:devfreq_frequency,devfreq:devfreq_monitor,'\
            'power:clock_set_rate'

    def __init__(self, workloads:[WorkloadRecord], iterations:int, set_bigcore:bool) -> None:
        """Constructor, initialized with list of workloads"""
        self.__workload_count = len(workloads)
        self.__workloads = []
        self.__resultsfile = []
        if (set_bigcore == True):
            taskset_cmd = self.__task_cmd_prefix + self.__task_cmd_option_bigcores 
        else:
            taskset_cmd = self.__task_cmd_prefix + self.__task_cmd_option_littlecores

        for item in workloads:
            results_file = 'results/'+item.name()+'.prof'
            workload_cmd_temp = self.__perf_stat_cmd_prefix +' '\
                            + self.__perf_stat_cmd_result_options + results_file +' '\
                            + self.__perf_stat_cmd_sampling_options +' '\
                            + self.__perf_stat_cmd_cpu_options +' '\
                            + self.__perf_stat_cmd_repeat_options + str(iterations) +' '\
                            + '-e ' + self.__perf_event_listing +' '\
                            + taskset_cmd + ' '\
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
        
    def push_dependent_files(self, workload_data:str) -> None:
        print ('Pushing dependencies to device... Please wait')
        self.__ssh_fabric_con.run ('mkdir -p bench-data')
        # Clean the old files - if any
        with self.__ssh_fabric_con.cd('bench-data/'):
            self.__ssh_fabric_con.run ('rm -rf *')

        
        self.__ssh_fabric_con.put(workload_data+'/Silent Love-360p.mp4','bench-data/')
        self.__ssh_fabric_con.put(workload_data+'/Silent Love-720p.mp4','bench-data/')
        self.__ssh_fabric_con.put(workload_data+'/cantrbry.zip','bench-data/')
        self.__ssh_fabric_con.put(workload_data+'/enwik8.zip','bench-data/')
        self.__ssh_fabric_con.put(workload_data+'/webster.bz2','bench-data/')

        print ('Extracting files... Please wait')
        with self.__ssh_fabric_con.cd('bench-data/'):
            self.__ssh_fabric_con.run ('bzip2 -d webster.bz2')
            self.__ssh_fabric_con.run ('unzip enwik8.zip')
            self.__ssh_fabric_con.run ('unzip cantrbry.zip')
            self.__ssh_fabric_con.run ('rm -f cantrbry.zip enwik8.zip')


    def batch_execute(self, results_dir:str) -> None:
        """Sequentially Execute the workloads"""

        with self.__ssh_fabric_con.cd('bench-data/'):
            ## Create results directory
            self.__ssh_fabric_con.run ('mkdir -p results/')
            workload_ctr = 0
            total_workload = len(self.__workloads)
            ## Iterate and execute each jobs
            for workload_item in self.__workloads:
                workload_ctr += 1
                result = workload_item[0]
                cmd = workload_item[1]
                print ('======= Workload ('+str(workload_ctr)+'/'+str(total_workload)+'): '+result +'=======')
                print('results file==> '+result)

                ## Start sampling via SmartPower3
                self.__powerMonSampler.StartSampling(results_dir+'/'+os.path.basename(result)+'.powdata')

                ## Execute the workload on device
                self.__ssh_fabric_con.run(cmd)

                ## Stop power data sampling from SmartPower3
                self.__powerMonSampler.StopSampling()

                ## Fetch results from remote
                self.__ssh_fabric_con.get('bench-data/'+result, results_dir+'/'+os.path.basename(result))

    def reboot_device (self)-> None:
        self.__ssh_fabric_con.run('reboot',warn=True)
        self.__ssh_fabric_con.close()
        time.sleep(15)
        while (True):
            try:
                # time.sleep(60)
                result = self.__ssh_fabric_con.run('echo -n')
                if result.return_code == 0:
                    print('--Complete--')
                    break
            except:
                print ('.', end ="")


    def setup_frequencies (self,cpufreq:int)-> None:
        # Setting Big Cor frequencies - will add governor configurations later
        self.__ssh_fabric_con.run('echo \''+str(cpufreq)+'\'> /sys/devices/system/cpu/cpu4/cpufreq/scaling_max_freq')

    def cleanup (self)-> None:
        # Clean the old files - if any
        with self.__ssh_fabric_con.cd('bench-data/'):
            self.__ssh_fabric_con.run ('rm -rf *')

## --------------------------------------------    
def Run_Workload(test_desc_suffix:str,
                 cpu_freq:int = 2000000,
                 iteration_count:int = 10,
                 enable_stress_workloads:bool = True, 
                 enable_compress_workloads:bool = True, 
                 enable_encode_workloads:bool = True                 
                 ) -> None:
    ## List out the workloads
    workload_listing = []
    ###################### Stress workloads - BEGIN ######################
    if (enable_stress_workloads == True):
        ### ------------ CPU Only workloads ------------ 
        workload_listing.append(WorkloadRecord('stress-cpu1-100s', 'stress','-c 1 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu2-100s', 'stress','-c 2 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu3-100s', 'stress','-c 3 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu4-100s', 'stress','-c 4 -t 100s'))
        ### ------------ IO Only workloads ------------ 
        workload_listing.append(WorkloadRecord('stress-io1-100s', 'stress','-i 1 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-io2-100s', 'stress','-i 2 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-io3-100s', 'stress','-i 3 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-io4-100s', 'stress','-i 4 -t 100s'))
        ### ------------  CPU & IO Only workloads ------------ 
        workload_listing.append(WorkloadRecord('stress-cpu_io1-100s', 'stress','-c 1 -i 1 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu_io2-100s', 'stress','-c 2 -i 2 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu_io3-100s', 'stress','-c 3 -i 3 -t 100s'))
        workload_listing.append(WorkloadRecord('stress-cpu_io4-100s', 'stress','-c 4 -i 4 -t 100s'))
    ###################### Stress workloads - END   ######################

    #################### Compression Workloads - BEGIN   ####################
    if (enable_compress_workloads == True):
        workload_listing.append(WorkloadRecord('bzip2-webster','bzip2','-k -f webster'))
        workload_listing.append(WorkloadRecord('bzip2-enwik8','bzip2','-k -f enwik8'))
        workload_listing.append(WorkloadRecord('gzip-webster','gzip','-k -f webster'))
        workload_listing.append(WorkloadRecord('gzip-enwik8','gzip','-k -f enwik8'))
        workload_listing.append(WorkloadRecord('xz-webster','xz','-k -f webster'))
        workload_listing.append(WorkloadRecord('xz-enwik8','xz','-k -f enwik8'))
    #################### Compression Workloads - END     ####################

    ############## FFMPEG Encode/Decode Workloads - BEGIN   ##################
    if (enable_encode_workloads == True):
        workload_listing.append(WorkloadRecord('ffmpeg-360p','ffmpeg',
                    '-i \'Silent Love-360p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
        workload_listing.append(WorkloadRecord('ffmpeg-720p','ffmpeg',
                    '-i \'Silent Love-720p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
    ############## FFMPEG Encode/Decode Workloads - END     ##################
    
    ## Compile the workload list & initialize the job
    workloads_obj = Workloads(workload_listing, iterations=iteration_count, set_bigcore=True)
    workloads = WorkloadManager(dev_ipaddr='192.168.0.101',
                        dev_user = 'root',
                        dev_pass = 'odroid',
                        workloads = workloads_obj
                        )
    
    ## Time stamp to segregate test runs
    test_run_name= datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S_'+test_desc_suffix)
    print (test_run_name)

    ## Create top level results directory
    parent_dirname = os.curdir
    results_dir_path = os.path.join(parent_dirname,'results')
    if (os.path.exists(results_dir_path) == False):
        os.mkdir(results_dir_path)

    ## Create timestamped directory under results directory holding specific test run
    results_dirname = 'results/'+test_run_name
    results_path = os.path.join(results_dir_path,test_run_name)
    if (os.path.exists(results_path) == False):
        os.mkdir(results_path)

    ###########################################################################
    # 1) Push required files to device
    # 2) Issue reboot to device
    # 3) Wait for device to be booted up, wait for 5 minutes, for things to settle
    # 4) Setup device - governors, CPU frequency configurations
    # 5) Wait for 2 minutes
    # 6) Run Workload & pull tar.bz2 results
    # 7) cleanup & go to step#2 until workload list/precondition list in empty
    ###########################################################################

    workload_data = os.path.join(parent_dirname,'data')
    print('Pushing dependant files')
    
    ### Step-1
    workloads.push_dependent_files(workload_data)
    print('File push completed, waiting for few seconds...')
    time.sleep(5)

    ## Step-2
    print('Rebooting device...')
    print('Waiting for device to be online...')
    workloads.reboot_device()
    print('Device back online...')

    ## Step-3
    print('Waiting for 5 mins...')
    time.sleep(5*60)
    print('Device Online & setting up frequency to '+str(cpu_freq))
    workloads.setup_frequencies(cpu_freq)
    
    print('Waiting for 2 mins...')
    time.sleep(2*60)
    
    # ## Execute the workload and gather results
    print('Initiating workloads')
    workloads.batch_execute(results_dirname)

    print('Workloads completed, cleanup and reboot...')
    workloads.cleanup()

    ## Cleanup
    del workloads
    del workloads_obj
    del workload_listing

## ----------------------------------------------------------------------------
# For now just sticking to performance governor, not schedutil governor
bigcore_freq_list = [2000000, 1900000, 1800000, 1700000, 1600000, 1500000, 1400000, 1300000 , 1200000 ]

if __name__ == '__main__':
    test_desc_prefix='BigCore-10itr-50msSmplg'
    for freq in bigcore_freq_list:
        test_desc_composed=test_desc_prefix+'-CPUFreq-'+str(freq/1000000)+'GHz'
        Run_Workload(test_desc_composed, cpu_freq=freq, iteration_count=10,
                     enable_stress_workloads= True,
                     enable_compress_workloads = False,
                     enable_encode_workloads = False )
