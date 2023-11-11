#!/usr/bin/env python3
import fabric
import time
import os
import datetime

## Import the local packages
from pathlib import Path
import sys
path_root = Path(__file__).parents[0]
# print (str(path_root))
sys.path.append(str(path_root))

from ODroidXU4.mgmt.BoardConfigControl import BroadConfig as hwctrl
from ODroidXU4.mgmt.performance.FanControl import FanControl as hwfan
from ODroidXU4.mgmt.performance.CPUFreq import CPUFreqControl as cpufreqctrl
from ODroidXU4.mgmt.performance.MemoryController import MemCtrlrFreqControl as memfreqctrl
from ODroidXU4.polling_sampler import DataSampler as  polling
from SmartPower3.SmartPower3 import NCSampler as sm3

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


class PerfStat_WorkloadCompiler:
    """Class to handle list of workloads"""
    
    # Perf Command options breakdown
    __perf_stat_cmd_prefix='sudo perf stat'
    __perf_stat_cmd_repeat_options='-r ' 
    ## Summarize the status at the end of the file
    __perf_stat_cmd_result_options='--summary -o '    
    # Sample at 50ms interval
    __perf_stat_cmd_sampling_options='-I 100 '
    # System wide and provide per core stats
    __perf_stat_cmd_cpu_options='-a --per-core' 
    
    __task_cmd_prefix='taskset '
    ## assigning to a single core than a range of CPU as --pre-core will show core-wise 
    ## analysis need to be core level 
    __task_cmd_option_bigcores=' -c 4,5,6,7 '
    __task_cmd_option_littlecores=' -c 1,2,3 ' 

    ## Perf events to be monitored.
    __perf_event_listing=\
            'branch-instructions,branch-misses,branch-load-misses,branch-loads,'\
            'bus-cycles,cpu-cycles,instructions,'\
            'cache-misses,cache-references,'\
            'cpu-clock,'\
            'L1-dcache-load-misses,L1-dcache-loads,L1-dcache-store-misses,L1-dcache-stores,'\
            'L1-icache-load-misses,L1-icache-loads,'\
            'LLC-load-misses,LLC-loads,LLC-store-misses,LLC-stores'

    def __init__(self, workloads:[WorkloadRecord], 
                 iterations:int, 
                 set_bigcore:bool,
                 results_prefix_dir:str='results'
                 ) -> None:
        """Constructor, initialized with list of workloads"""
        self.__workload_count = len(workloads)
        self.__workloads = []
        self.__resultsfile = []
        if (set_bigcore == True):
            taskset_cmd = self.__task_cmd_prefix + self.__task_cmd_option_bigcores 
        else:
            taskset_cmd = self.__task_cmd_prefix + self.__task_cmd_option_littlecores

        for item in workloads:
            results_file = results_prefix_dir+'/'+item.name()+'.prof'
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
        """
        return self.__workload_count
    

    def __iter__ (self):
        """To support iteration of workload list
        """
        self.__itr_ctr = 0
        return self
    
    def __next__(self):
        """Iterate through the workload list elements
        """
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


#################################################
############## Workload Base class ##############
#################################################
class WorkloadBase:
    def __init__(self, 
                 conn: fabric.Connection,
                 run_on_bigcore: bool = True,
                 ):
        self.__conn__    = conn
        self.__run_on_bigcore__ = run_on_bigcore
        
        # Initialize hardware controller modules
        self.__bdctrl__  = hwctrl(self.__conn__)
        self.__fanctrl__ = hwfan(self.__conn__)
        self.__perfcpuctrl__ = cpufreqctrl(self.__conn__)
        self.__perfmemctrl__ = memfreqctrl(self.__conn__)

        # Initialize data samplers
        self.__polling__ = polling(self.__conn__)
        self.__sm3__     = sm3()

    def __setup_persistant__(self,
                    resultsdir_prefix:str,
                    testname_suffix:str):
        # Set CPU isolation prior to reboot so that CPUs are reserved for 
        # workload execution
        if (self.__run_on_bigcore__):
            print ('Setting Big cluster isolation')
            self.__bdctrl__.set_cpuisol_bigcluster()
        else:
            print ('Setting Little cluster isolation')
            self.__bdctrl__.set_cpuisol_littlecluster()

        
        # Setup for results storage
        ## Time stamp to segregate test runs
        test_run_name= datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S_'+testname_suffix)
        print (test_run_name)

        ## Create top level results directory
        if (os.path.exists(resultsdir_prefix) == False):
            os.mkdir(resultsdir_prefix)

        ## Create timestamped directory under results directory holding specific test run
        self.__results_path__ = os.path.join(resultsdir_prefix,test_run_name)
        if (os.path.exists(self.__results_path__) == False):
            os.mkdir(self.__results_path__)

        # Initiate reboot
        time.sleep(2)
        self.__bdctrl__.reboot_device()

    def __pre_run__(self,tc_opres_file:str,
                    cpu_freq:int = 2000000):
        ## HW Setup & necessary preconditions to be added here, which are to be done
        ## prior to starting test run
        # Let the fan run always..
        self.__fanctrl__.switch_on()
        # Setup up cluster frequency for either big or little cores
        if (self.__run_on_bigcore__):
            print ('Setting Big cluster\'s frequency configurations')
            self.__perfcpuctrl__.set_cluster_gov_perf(True)
            self.__perfcpuctrl__.set_cluster_frequency(True,cpu_freq)
        else:
            print ('Setting Little cluster\'s frequency configurations')
            self.__perfcpuctrl__.set_cluster_gov_perf(False)
            self.__perfcpuctrl__.set_cluster_frequency(False,cpu_freq)
        
        # Setup up memory controller performance
        self.__perfmemctrl__.set_governor_perf()
        self.__perfmemctrl__.set_boost_max_freq()

        print('Waiting for 2 mins...')
        time.sleep(2*60)
        print ('__pre_run__: '+ tc_opres_file + ' @'+str(cpu_freq))

        ## Start the data samplers
        self.__sm3__.StartSampling(self.__results_path__+'/'+os.path.basename(tc_opres_file) +'.powdata')
        self.__polling__.StartSampling(self.__results_path__+'/'+os.path.basename(tc_opres_file)+'.polldata')
        

    def __post_run__(self):
        ## Stop data samplers
        self.__sm3__.StopSampling()
        self.__polling__.StopSampling()

        # Cleanup code of files and HW after test execution
        pass

        

#################################################
##############   CPU workload(s)   ##############
#################################################

class CPUIntensiveWorkloads(WorkloadBase):
    def __init__(self, conn: fabric.Connection,
                 iteration_count:int = 10,
                 run_on_bigcore: bool = True,
                 enable_stress_workloads:bool = True, 
                 enable_compress_workloads:bool = False, 
                 enable_encode_workloads:bool = False
                 ):
        WorkloadBase.__init__(self,conn,run_on_bigcore=run_on_bigcore)
        self.workload_listing = []
        self.run_on_bigcore = run_on_bigcore

        self.iteration_count = iteration_count
        self.enable_stress_workloads = enable_stress_workloads 
        self.enable_compress_workloads = enable_compress_workloads
        self.enable_encode_workloads = enable_encode_workloads

        self.__compile_workloadlist__()

    def __compile_workloadlist__ (self):
        ##################### Stress workloads - BEGIN ######################
        if (self.enable_stress_workloads == True):
            ### ------------ CPU Only workloads ------------ 
            self.workload_listing.append(WorkloadRecord('stress-cpu1-100s', 'stress','-c 1 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu2-100s', 'stress','-c 2 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu3-100s', 'stress','-c 3 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu4-100s', 'stress','-c 4 -t 100s'))
            ### ------------ IO Only workloads ------------ 
            self.workload_listing.append(WorkloadRecord('stress-io1-100s', 'stress','-i 1 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io2-100s', 'stress','-i 2 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io3-100s', 'stress','-i 3 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io4-100s', 'stress','-i 4 -t 100s'))
            ### ------------  CPU & IO Only workloads ------------ 
            self.workload_listing.append(WorkloadRecord('stress-cpu_io1-100s', 'stress','-c 1 -i 1 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu_io2-100s', 'stress','-c 2 -i 2 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu_io3-100s', 'stress','-c 3 -i 3 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu_io4-100s', 'stress','-c 4 -i 4 -t 100s'))
        ###################### Stress workloads - END   ######################

        #################### Compression Workloads - BEGIN   ####################
        if (self.enable_compress_workloads == True):
            self.workload_listing.append(WorkloadRecord('bzip2-webster','bzip2','-k -f webster'))
            self.workload_listing.append(WorkloadRecord('bzip2-enwik8','bzip2','-k -f enwik8'))
            self.workload_listing.append(WorkloadRecord('gzip-webster','gzip','-k -f webster'))
            self.workload_listing.append(WorkloadRecord('gzip-enwik8','gzip','-k -f enwik8'))
            self.workload_listing.append(WorkloadRecord('xz-webster','xz','-k -f webster'))
            self.workload_listing.append(WorkloadRecord('xz-enwik8','xz','-k -f enwik8'))
        #################### Compression Workloads - END     ####################

        ############## FFMPEG Encode/Decode Workloads - BEGIN   ##################
        if (self.enable_encode_workloads == True):
            self.workload_listing.append(WorkloadRecord('ffmpeg-360p','ffmpeg',
                        '-hide_banner -loglevel warning -i \'Silent Love-360p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
            self.workload_listing.append(WorkloadRecord('ffmpeg-720p','ffmpeg',
                        '-hide_banner -loglevel warning -i \'Silent Love-720p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
        ############## FFMPEG Encode/Decode Workloads - END     ##################
        
        ## Compile the workload list & initialize the job
        self.workloads_obj = PerfStat_WorkloadCompiler(self.workload_listing, 
                                    iterations=self.iteration_count,
                                    set_bigcore=self.run_on_bigcore)
    
    def setup_persistant(self,workload_data:str, 
                            resultsdir_prefix:str,
                            testname_suffix:str):
        print ('Pushing dependencies to device... Please wait')
        self.__conn__.run ('mkdir -p bench-data')
        # Clean the old files - if any
        with self.__conn__.cd('bench-data/'):
            self.__conn__.run ('rm -rf *')

        self.__conn__.put(workload_data+'/Silent Love-360p.mp4','bench-data/')
        self.__conn__.put(workload_data+'/Silent Love-720p.mp4','bench-data/')
        self.__conn__.put(workload_data+'/cantrbry.zip','bench-data/')
        self.__conn__.put(workload_data+'/enwik8.zip','bench-data/')
        self.__conn__.put(workload_data+'/webster.bz2','bench-data/')

        print ('Extracting files... Please wait')
        with self.__conn__.cd('bench-data/'):
            self.__conn__.run ('bzip2 -d webster.bz2')
            self.__conn__.run ('unzip enwik8.zip')
            self.__conn__.run ('unzip cantrbry.zip')
            self.__conn__.run ('rm -f cantrbry.zip enwik8.zip')
        
        # Calling base class for generic actions & reboot
        WorkloadBase.__setup_persistant__(self, resultsdir_prefix, testname_suffix)

    def __pre_run__(self,
                    tc_name:str,
                    cpu_freq:int = 2000000,
                    ):
        ''' Method to be exceuted prior to running CPU workloads
        '''
        WorkloadBase.__pre_run__(self, tc_name, cpu_freq) # Calling base class for generic actions
        

    def __post_run__(self):
        ''' Method to be exceuted after running CPU workloads
        '''
        WorkloadBase.__post_run__(self)
    
    def run(self,
            cpu_freq:int = 2000000,
            ) -> str:
        
        # print (test_run_name)
        with self.__conn__.cd('bench-data/'):
            ## Create results directory
            self.__conn__.run ('mkdir -p results/')
            workload_ctr = 0
            total_workload = len(self.workloads_obj)
            ## Iterate and execute each jobs
            for workload_item in self.workloads_obj:
                workload_ctr += 1
                result = workload_item[0]
                cmd = workload_item[1]

                self.__pre_run__(result, cpu_freq)
                print ('======= Workload ('+str(workload_ctr)+'/'+str(total_workload)+'): '+result +'=======')
                print('results file==> '+result)
                ## Execute the workload on device
                self.__conn__.run(cmd)
                self.__post_run__()

                ## Fetch results from remote
                self.__conn__.get('bench-data/'+result, self.__results_path__+'/'+os.path.basename(result))
        return self.__results_path__

        

#################################################
##############  Idling workload(s) ##############
#################################################
class Idle_WorkloadCompiler(WorkloadBase):
    def __init__(self, conn: fabric.Connection):
        WorkloadBase.__init__(conn)


#### ==========================================================================
#### Test Code
# if __name__ == '__main__':
#     src_root = Path(__file__).parents[1]
#     print(src_root)
#     workload_data_dir = os.path.join(src_root,'data')
#     workload_result_dir = os.path.join(src_root,'results')

#     conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
#     cpuload_wkld = CPUIntensiveWorkloads(conn)
#     cpuload_wkld.setup_persistant(workload_data=workload_data_dir, resultsdir_prefix=workload_result_dir, testname_suffix='dummy-2GHz')
#     cpuload_wkld.run( )
    
#     del cpuload_wkld

#### ==========================================================================