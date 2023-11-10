#!/usr/bin/env python3
import fabric

class FanControl:
    ''' Wrapper class for controlling CPU Fan on ODroid-XU4 hardware
    '''
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        self.__fanctrl_path__ = '/sys/devices/platform/pwm-fan'

        fanspeeds_ret = self.__conn__.run('cat '+self.__fanctrl_path__+'/fan_speed', hide="stdout")
        if fanspeeds_ret:
            self.__fanspeeds__ = fanspeeds_ret.tail('stdout',1).strip().split(' ')
            #the fanspeeds will be like values : 0 120 180 240
            # implying higher indices for max speeds
            ## print (fanspeeds)
            self.__off_speed_idx__ = 0
            self.__off_speed__ = self.__fanspeeds__[self.__off_speed_idx__]
            self.__max_speed_idx__ = len(self.__fanspeeds__) -1
            self.__max_speed__ = self.__fanspeeds__[self.__max_speed_idx__]
        else:
            raise Exception('Fan speed parameters seemt to be not accessible')
        
        # Disable automatic fan control, will enable it back later
        self.__conn__.run('echo 0 > '+self.__fanctrl_path__+'/automatic')
        self.switch_off()
        
    
    def __del__(self):
        self.switch_off()
        self.__conn__.run('echo 1 > '+self.__fanctrl_path__+'/automatic')

    def switch_off(self):
        self.__conn__.run('echo '+self.__off_speed__+' > '+self.__fanctrl_path__+'/pwm1')

    def switch_on(self):
        self.__conn__.run('echo '+self.__max_speed__+' > '+self.__fanctrl_path__+'/pwm1')

    def __check_state__(self):
        pwmval = self.__conn__.run('cat '+self.__fanctrl_path__+'/pwm1', hide="stdout")
        if pwmval:
            gov = pwmval.tail('stdout',1).strip()
            return int(gov)


#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    import time
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    fc = FanControl(conn)
    print ('Fan switch OFF test..')
    fc.switch_off()
    time.sleep(2)
    assert fc.__check_state__() == 0,'Fan state mismatching from OFF, which was expected'

    print ('Fan switch ON test..')
    fc.switch_on()
    time.sleep(2)
    assert fc.__check_state__() != 0,'Fan state mismatching from On, which was expected'

    print ('Fan switch OFF test..')
    fc.switch_off()
    time.sleep(2)
    assert fc.__check_state__() == 0,'Fan state mismatching from OFF, which was expected'

    print ('Test completed succesfully ...')

#### ==========================================================================