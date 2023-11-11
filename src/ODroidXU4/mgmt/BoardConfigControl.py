#!/usr/bin/env python3
import fabric
import time

## Import the local packages
from pathlib import Path
import sys
path_root = Path(__file__).parents[3]
sys.path.append(str(path_root))
from src.utils import ProgressBar

class BroadConfig:
    ''' Wrapper class for controlling Boot up configuration management
    '''
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        
        self.__bootconfig_filepath__ = '/media/boot/boot.ini'
        self.__isolconf_cmd_clear__ = 'sed -i \'s/^setenv isolcpus_list/#setenv isolcpus_list/g\' '+self.__bootconfig_filepath__
        self.__isolconf_sedcmd_bigcluster__ = 'sed -i \'s/^#\{0,1\}setenv isolcpus_list .*"/setenv isolcpus_list "4,5,6,7"/g\' '+self.__bootconfig_filepath__
        self.__isolconf_sedcmd_littlecluster__ = 'sed -i \'s/^#\{0,1\}setenv isolcpus_list .*/setenv isolcpus_list "1,2,3"/g\' '+self.__bootconfig_filepath__

    def set_cpuisol_bigcluster(self):
        cmd =self.__isolconf_sedcmd_bigcluster__
        # print(cmd)
        self.__conn__.run(cmd)

    def set_cpuisol_littlecluster(self):
        cmd = self.__isolconf_sedcmd_littlecluster__
        # print(cmd)
        self.__conn__.run(cmd)

    def clear_cpuisol(self):
        cmd = self.__isolconf_cmd_clear__
        # print(cmd)
        self.__conn__.run(cmd)

    def __get_next_cpuisolconf__(self):
        isolval = self.__conn__.run('grep "#setenv isolcpus_list" '+self.__bootconfig_filepath__, warn = True, hide='stdout')
        if isolval:
            return ''
        else:
            isolval = self.__conn__.run('grep "setenv isolcpus_list" '+self.__bootconfig_filepath__, warn = True, hide='stdout')
            if (isolval):
                val = isolval.tail('stdout',1).strip().split(' ')[2].strip('"')
                return str(val)

    def __get_cur_cpuisolconf__(self):
        isolval = self.__conn__.run('cat /sys/devices/system/cpu/isolated', hide='stdout')
        if isolval:
            gov = isolval.tail('stdout',0).strip().strip('"')
            return str(gov)
        else:
            return ''
    
    def reboot_device (self)-> None:
        self.__conn__.run('reboot',warn=True)
        self.__conn__.close()
        print ('--- Waiting for device ---')
        time.sleep(10)
        while (True):
            try:
                result = self.__conn__.run('echo -n')
                if result.return_code == 0:
                    print('--Complete--')
                    break
            except:
                print ('.', end ="")

#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    bc = BroadConfig(conn)

    print ('Current isolation config: '+str(bc.__get_cur_cpuisolconf__()))
    print ('Next boot isolation config: '+str(bc.__get_next_cpuisolconf__()))
    print ('Change isolation config to little cluster...')
    bc.clear_cpuisol()
    bc.set_cpuisol_littlecluster()
    assert bc.__get_next_cpuisolconf__() == '1,2,3', 'Failure in setting isolation configuration for next boot to little cluster'
    print ('Next boot isolation config: '+str(bc.__get_next_cpuisolconf__()))
    print ('Rebooting device to check effect...')
    bc.reboot_device()
    assert bc.__get_cur_cpuisolconf__() == '1-3', 'Failure in rebooted isolation configuration to little cluster'

    print ('Change isolation config to big cluster...')
    bc.set_cpuisol_bigcluster()
    assert bc.__get_next_cpuisolconf__() == '4,5,6,7', 'Failure in setting isolation configuration for next boot to little cluster'
    print ('Next boot isolation config: '+str(bc.__get_next_cpuisolconf__()))
    print ('Rebooting device to check effect...')
    bc.reboot_device()
    assert bc.__get_cur_cpuisolconf__() == '4-7', 'Failure in rebooted isolation configuration to big cluster'

    print ('Board boot configuration test completed...')

#### ==========================================================================