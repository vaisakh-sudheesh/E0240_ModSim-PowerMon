import os
import threading
import subprocess
import signal
import sys
import time
import re
import telnetlib
import pexpect

gem5_working_dir = os.path.abspath('simulation/working-dir')
gem5_bindist_dir = os.path.abspath('simulation/gem5-dist')
print ('Working dir: '+gem5_working_dir  +'Gem5 binary dist: '+gem5_bindist_dir)


gem5_executable_file            = gem5_bindist_dir+'/gem5.opt'
# Simulation configuration script
gem5_args_script                = '../gem5-src/configs/example/arm/odroid_xu4_sim.py'
# Images
gem5_args_kernel                = '--kernel ../plat-resource/vmlinux'
gem5_args_bootlader             = '--bootloader ../plat-resource/boot'
gem5_args_ubuntuimg             = '--disk ../plat-resource/ubuntu-18.04-docker.img'
# Platform/Chip configuration
gem5_args_cpu_config            = '--cpu-type exynos --machine-type VExpress_GEM5  --big-cpus 4 --little-cpus 4'
gem5_args_memory_config         = '--caches --mem-size 2GB'
gem5_args_freq_configs          = '--big-cpu-clock 2.0GHz --big-cpu-voltage 1.25V --little-cpu-clock 1.4GHz --little-cpu-voltage 1.25V'
# Checkpoint configuration
gem5_args_checkpoint_config     = '--restore m5out/cpt.328949930500/'

stdout = None
stderr = None
proc = None
thread_gem5 = None
exit_gem5 = False
telnet_thread = None
re_shell_prompt  = re.compile('^root@aarch64-gem5:(.*)#')

def _gem5_term_wait_untilshell(telnet_session,):
    telnet_session.read_until(b"root@aarch64-gem5:")
    print('Sim-Host: Shell ready')    
    telnet_session.write('m5 resetstats && ls && m5 dumpstats && m5 exit'.encode('ascii') + b"\n")
    print('Sim-Host: Initiated workload')
    print(telnet_session.read_all().decode('ascii'))
    print('Sim-Host: Workload execution completed & gem5 exiting with m5 exit')

def gem5_sim_thread():
    re_term_ready_string ='system.terminal: Listening for connections on port 3456'
    cmdline = gem5_executable_file + \
                    ' ' + gem5_args_script + \
                    ' ' + gem5_args_kernel + ' ' + gem5_args_bootlader + ' ' + gem5_args_ubuntuimg + \
                    ' ' + gem5_args_cpu_config + ' ' + gem5_args_memory_config + ' ' + gem5_args_freq_configs + \
                    ' ' + gem5_args_checkpoint_config

    proc = pexpect.spawn(cmdline, cwd=gem5_working_dir,)
    proc.expect(re_term_ready_string)
    print('Sim-Host: Gem5 Simulation ready for connection')   
    # Start the telnet thread
    telnet_session = telnetlib.Telnet('localhost', 3456)
    time.sleep(4)
    telnet_thread = threading.Thread(target=_gem5_term_wait_untilshell, args=(telnet_session,))
    telnet_thread.start()
    proc.wait()
    print('Sim-Host[STDERR]: Gem5 exited')


def signal_handler(signum, frame):
    print ('Signal recieved')
    exit_gem5 = True
    if (proc != None):
        proc.kill()
    thread_gem5.join()
    

def run_simulation():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    gem5_sim_thread()


if __name__ == '__main__':
    run_simulation()