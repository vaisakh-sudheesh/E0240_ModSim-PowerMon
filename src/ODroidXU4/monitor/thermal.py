#!/usr/bin/env python3
import fabric

class ThermalSampler:
    '''Wrapper class for thermal data sampling

    More information on thermal sysfs can be found in https://docs.kernel.org/driver-api/thermal/sysfs-api.html
    '''
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        self.__csv_header__ = ['therm_cpu0','therm_cpu1','therm_cpu2','therm_cpu4']
        self.__csv_fieldcnt__ = len(self.__csv_header__)
    
    def header(self) ->[str]:
        '''Returns header to be used for CSV file
        '''
        return self.__csv_header__


    def sample_data(self) -> [int]:
        '''Returns list of timestamp-ed(utc & local) csv strings to be recorded 
        '''
        with self.__conn__.cd('/sys/devices/virtual/thermal/'):
            thermstat  = self.__conn__.run(
                                'echo $(cat'\
                                ' thermal_zone0/temp'\
                                ' thermal_zone1/temp'\
                                ' thermal_zone2/temp'\
                                ' thermal_zone3/temp)',
                             hide='stdout')
        
        
        if thermstat:
            cpustat_stdout = thermstat.tail('stdout',1).strip()
            csved = [eval(i) for i in cpustat_stdout.split(' ')] 
            test_len = len(csved)
            assert test_len == (self.__csv_fieldcnt__), \
                                'Final length of CSV record seems to be wrong as '\
                                +str(test_len)+\
                                ', expected: '+str(self.__csv_fieldcnt__)
            return csved
        else:
            return []
        
#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    import time
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    procstat = ThermalSampler(conn)
    
    csv_header = procstat.header()
    print('CSV Header: '+str(csv_header))
    ##TODO: Add assertion for testing csv formatted data of N number of fields

    procstat_cpu = procstat.sample_data()
    print('CSV Data: '+str(procstat.sample_data()))
    ##TODO: Add assertion for testing csv formatted data of N number of fields
    
    print ('Thermal Stat test completed...')

#### ==========================================================================
