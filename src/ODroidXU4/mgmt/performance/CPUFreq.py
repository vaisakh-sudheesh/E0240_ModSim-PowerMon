#!/usr/bin/env python3
import fabric

class CPUFreqControl:
    ''' Wrapper class for controlling CPU Frequency on ODroid-XU4
    '''
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn

        self.__bigcorectrl_path__               = '/sys/devices/system/cpu/cpufreq/policy4'
        self.__bigcluster_governor_filename__   = self.__bigcorectrl_path__+'/scaling_governor'
        self.__bigcluster_max_filename__        = self.__bigcorectrl_path__+'/scaling_max_freq'

        self.__littlecorectrl_path__            = '/sys/devices/system/cpu/cpufreq/policy0'
        self.__litcluster_governor_filename__   = self.__littlecorectrl_path__+'/scaling_governor'
        self.__litcluster_max_filename__        = self.__littlecorectrl_path__+'/scaling_max_freq'

    def set_cluster_gov_perf(self, bigcluster: bool) -> None:
        file = self.__bigcluster_governor_filename__ if (bigcluster) else self.__litcluster_governor_filename__
        self.__conn__.run('echo performance> '+ file)

    def set_cluster_gov_schedutil(self, bigcluster: bool) -> None:
        file = self.__bigcluster_governor_filename__ if (bigcluster) else self.__litcluster_governor_filename__
        self.__conn__.run('echo schedutil> '+ file)

    def set_cluster_gov_ondemand(self, bigcluster: bool) -> None:
        file = self.__bigcluster_governor_filename__ if (bigcluster) else self.__litcluster_governor_filename__
        self.__conn__.run('echo ondemand> '+ file)

    def set_cluster_frequency (self, bigcluster: bool, cpufreq:int)-> None:
        file = self.__bigcluster_max_filename__ if (bigcluster) else self.__litcluster_max_filename__
        self.__conn__.run('echo \''+str(cpufreq)+'\'> '+ file)

    def __get_cluster_governor__(self, bigcluster: bool) -> str :
        file = self.__bigcluster_governor_filename__ if (bigcluster) else self.__litcluster_governor_filename__
        govval = self.__conn__.run('cat '+ file, hide="stdout")
        if (govval):
            gov = govval.tail('stdout',1).strip()
            return str(gov)
        
    def __get_cluster_maxfreq__(self, bigcluster: bool) -> int :
        file = self.__bigcorectrl_path__ if (bigcluster) else self.__littlecorectrl_path__
        file = file + '/cpuinfo_cur_freq'
        govval = self.__conn__.run('cat '+ file, hide="stdout")
        if (govval):
            gov = govval.tail('stdout',1).strip()
            return int(gov)

#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    import time
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    freqctrl = CPUFreqControl(conn)
    
    ## Test cluster governor set to performance & validate
    time.sleep(2)
    freqctrl.set_cluster_gov_perf(False)
    assert freqctrl.__get_cluster_governor__(False) == 'performance','Performance governor setting failed for little cluster'
    freqctrl.set_cluster_gov_perf(True)
    assert freqctrl.__get_cluster_governor__(True) == 'performance','Performance governor setting failed for big cluster'

    ## Test cluster max frequency setting  & validate
    freqctrl.set_cluster_frequency(False, 1200000)
    assert freqctrl.__get_cluster_maxfreq__(False) == 1200000,'Little cluster max frequency setting failed'
    freqctrl.set_cluster_frequency(True, 1400000)
    assert freqctrl.__get_cluster_maxfreq__(True) == 1400000,'Big cluster max frequency setting-1 failed'
    freqctrl.set_cluster_frequency(True, 2000000)
    assert freqctrl.__get_cluster_maxfreq__(True) == 2000000,'Big cluster max frequency setting-2 failed'

    ## Test cluster governor set to schedutil & validate
    time.sleep(2)
    freqctrl.set_cluster_gov_schedutil(False)
    assert freqctrl.__get_cluster_governor__(False) == 'schedutil','schedutil governor setting failed for little cluster'
    freqctrl.set_cluster_gov_schedutil(True)
    assert freqctrl.__get_cluster_governor__(True) == 'schedutil','schedutil governor setting failed for little cluster'

    ## Test cluster governor set to ondemand & validate
    time.sleep(2)
    freqctrl.set_cluster_gov_ondemand(False)
    assert freqctrl.__get_cluster_governor__(False) == 'ondemand','ondemand governor setting failed for little cluster'
    freqctrl.set_cluster_gov_ondemand(True)
    assert freqctrl.__get_cluster_governor__(True) == 'ondemand','ondemand governor setting failed for little cluster'

    ## No assertion failures, hence test passed.
    print ('CPUFreq test completed...')

#### ==========================================================================