#!/usr/bin/env python3
import fabric

class MemCtrlrFreqControl:
    ''' Wrapper class for controlling Memory Controller Frequency on ODroid-XU4
    '''

    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        self.__memctrl_path__  = '/sys/class/devfreq/10c20000.memory-controller'
        self.__governor_file__ = self.__memctrl_path__+'/governor'
        self.__maxfreq_file__  = self.__memctrl_path__+'/max_freq'
        self.__minfreq_file__  = self.__memctrl_path__+'/min_freq'

        ##TODO: back up the current ones for restoration on object deletion

    def set_governor_perf(self):
        fanspeeds_ret = self.__conn__.run('echo performance > '+self.__governor_file__)

    def set_governor_ondemand(self):
        fanspeeds_ret = self.__conn__.run('echo simple_ondemand > '+self.__governor_file__)

    def set_governor_powersave(self):
        fanspeeds_ret = self.__conn__.run('echo powersave > '+self.__governor_file__)
        
    def set_boost_max_freq(self, val:int = 825000000):
        fanspeeds_ret = self.__conn__.run('echo '+str(val)+' > '+self.__maxfreq_file__)

    def __check_governor__(self):
        govval = self.__conn__.run('cat '+self.__governor_file__, hide="stdout")
        if govval:
            gov = govval.tail('stdout',1).strip()
            return str(gov)
        
    def __check_maxfreq__(self):
        govval = self.__conn__.run('cat '+self.__maxfreq_file__, hide="stdout")
        if govval:
            gov = govval.tail('stdout',1).strip()
            return int(gov)

#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    import time
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    mctrl = MemCtrlrFreqControl(conn)

    print ('Testing simple_ondemand governor setting')
    mctrl.set_governor_ondemand()
    assert mctrl.__check_governor__() == 'simple_ondemand', 'Govenor configured mismatched with simple_ondemand'

    time.sleep(2)
    print ('Testing powersave governor setting')
    mctrl.set_governor_powersave()
    assert mctrl.__check_governor__() == 'powersave', 'Govenor configured mismatched with powersave'

    time.sleep(2)
    print ('Testing performance governor setting')
    mctrl.set_governor_perf()
    assert mctrl.__check_governor__() == 'performance', 'Govenor configured mismatched with performance'

    for freq in [728000000, 206000000, 165000000, 165000000]:
        time.sleep(2)
        print ('Testing max frequency setting to '+ str(freq))
        mctrl.set_boost_max_freq(freq)
        time.sleep(1)
        assert mctrl.__check_maxfreq__() == freq, 'Max frequency configured mismatched with '+str(freq)

    print ('Memory controller performance control test completed succesfully...')

#### ==========================================================================