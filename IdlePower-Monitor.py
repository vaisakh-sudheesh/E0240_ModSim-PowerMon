#!/usr/bin/env python3
import fabric
import datetime
import time
import os
import tqdm

## Import the local packages
from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))
import src.PowerMon.SmartPower3 as sm3

class IdlePowerMonitor:
    def __init__(self, dev_ipaddr:str, dev_user:str, dev_pass:str) -> None:
        self.__dev_ipaddr = dev_ipaddr
        self.__dev_user = dev_user
        self.__dev_pass = dev_pass
        self.__ssh_fabric_con = fabric.Connection(
                ## SSH IP Address & Port
                self.__dev_ipaddr, port=22,
                ## Username & Password
                user=self.__dev_user, connect_kwargs={'password':self.__dev_pass})
        self.__powerMonSampler = sm3.NCSampler()


    def execute(self, result:str ,results_dir:str, idling_period_s: int = 60) -> None:
        ## Start sampling via SmartPower3
        print('Initiating Idling for '+str(idling_period_s)+' seconds')
        self.__powerMonSampler.StartSampling(results_dir+'/'+os.path.basename(result)+'.powdata')
        pbar = tqdm.tqdm(range(idling_period_s), bar_format='{desc} {percentage:3.0f}%|{bar}|{remaining} seconds')
        pbar.set_description("Idling")
        for i in pbar:
            time.sleep(1)
        ## Stop power data sampling from SmartPower3
        self.__powerMonSampler.StopSampling()


    def reboot_device (self)-> None:
        self.__ssh_fabric_con.run('reboot',warn=True)
        self.__ssh_fabric_con.close()
        time.sleep(15)
        while (True):
            try:
                result = self.__ssh_fabric_con.run('echo -n')
                if result.return_code == 0:
                    print('--Complete--')
                    break
            except:
                print ('.', end ="")


    def setup_frequencies (self,cpufreq:int)-> None:
        # Setting Big Cor frequencies - will add governor configurations later
        self.__ssh_fabric_con.run('echo \''+str(cpufreq)+'\'> /sys/devices/system/cpu/cpu4/cpufreq/scaling_max_freq')


scenario_exec = IdlePowerMonitor(dev_ipaddr='192.168.0.101', dev_user = 'root', dev_pass = 'odroid')

## --------------------------------------------
def Run_Scenario(test_desc_suffix:str, 
                 cpu_freq:int = 2000000,
                 idling_period_s:int = 60
                 ,iteration_count:int = 10) -> None:


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

    itr_ctr = 1
    while (itr_ctr <= iteration_count):
        print('Rebooting device...\nWaiting for device to be online...')
        scenario_exec.reboot_device()

        print('Device back online...\n Waiting for 5 mins to avoid initial measurement noise...')
        wait_s = 5*60
        sleep1_pbar = tqdm.tqdm(range(wait_s), bar_format='{desc} {percentage:3.0f}%|{bar}|{remaining} seconds')
        sleep1_pbar.set_description("Waiting")
        for i in sleep1_pbar:
            time.sleep(1)

        print('Device Online & setting up frequency to '+str(cpu_freq))
        scenario_exec.setup_frequencies(cpu_freq)

        print('Waiting for 1 min, prior to measurement...')
        wait_s = 1*60
        sleep2_pbar = tqdm.tqdm(range(wait_s), bar_format='{desc} {percentage:3.0f}%|{bar}|{remaining} seconds')
        sleep2_pbar.set_description("Waiting")
        for i in sleep2_pbar:
            time.sleep(1)

        # ## Execute the scenario and gather results
        print('Initiating Idling ')
        scenario_exec.execute(result = 'idle-itr-'+str(itr_ctr),results_dir=results_dirname, idling_period_s = idling_period_s)
        print('Idle measurement completed, cleanup and reboot...')

        itr_ctr += 1


## ----------------------------------------------------------------------------
# For now just sticking to performance governor, not schedutil governor
bigcore_freq_list = [2000000, 1900000, 1800000, 1700000, 1600000, 1500000, 1400000, 1300000 , 1200000 ]

if __name__ == '__main__':
    iterations = 10
    test_desc_prefix='Idling-BigCore-'+str(iterations)+'itr-50msSmplg-'
    for freq in bigcore_freq_list:
        test_desc_composed=test_desc_prefix+'CPUFreq-'+str(freq/1000000)+'GHz'
        Run_Scenario(test_desc_suffix=test_desc_composed, cpu_freq=freq, idling_period_s = (10*60), iteration_count=iterations)
