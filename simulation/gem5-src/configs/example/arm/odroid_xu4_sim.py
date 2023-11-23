import argparse
import os

import m5
from m5.objects import MathExprPowerModel, PowerModel

import fs_bigLITTLE as bL

class CpuPowerOn(MathExprPowerModel):
    def __init__(self, cpu_path,big_dyncoeff, big_statcoeff, **kwargs):
        super(CpuPowerOn, self).__init__(**kwargs)
        # <x>A per IPC and then convert to Watt
        print ('CpuPowerOn'+str(cpu_path)+', Dyn Coeff = '+big_dyncoeff+', Static Coeff = '+ big_statcoeff)
        self.dyn = (
            "voltage * ({} * {}.ipc)".format(big_dyncoeff, cpu_path)
        )
        self.st = (
            "voltage * ({} * 0.001 * {}.ipc)".format(big_statcoeff, cpu_path)
        )


class CpuPowerOff(MathExprPowerModel):
    dyn = "0"
    st = "0"


class CpuPowerModel(PowerModel):
    def __init__(self, cpu_path, big_dyncoeff, big_statcoeff, **kwargs):
        super(CpuPowerModel, self).__init__(**kwargs)
        self.pm = [
            CpuPowerOn(cpu_path, big_dyncoeff, big_statcoeff),  # ON
            CpuPowerOff(),  # CLK_GATED
            CpuPowerOff(),  # SRAM_RETENTION
            CpuPowerOff(),  # OFF
        ]

def addOptions(parser):
    parser.add_argument(
        "--bigcore-dyn-pow-coeff",
        type=str,
        default="1.0",
        help="Coefficient to be used in power model for Big Core's dynamic power",
    )
    parser.add_argument(
        "--bigcore-stat-pow-coeff",
        type=str,
        default="1.0",
        help="Coefficient to be used in power model for Big Core's static power",
    )
    parser.add_argument(
        "--littlecore-dyn-pow-coeff",
        type=str,
        default="1.0",
        help="Coefficient to be used in power model for Little Core's dynamic power",
    )
    parser.add_argument(
        "--littlecore-stat-pow-coeff",
        type=str,
        default="1.0",
        help="Coefficient to be used in power model for Little Core's static power",
    )


def main():
    parser = argparse.ArgumentParser(
        description="ODroid-XU4 Power Model"
    )
    addOptions(parser)
    bL.addOptions(parser)
    options = parser.parse_args()

    if options.cpu_type != "exynos":
        m5.fatal("The power script requires 'exynos' CPUs type to be used.")

    root = bL.build(options)

    big_dynamic_powcoeff = options.bigcore_dyn_pow_coeff
    big_static_powcoeff = options.bigcore_stat_pow_coeff

    little_dynamic_powcoeff = options.littlecore_dyn_pow_coeff
    little_static_powcoeff = options.littlecore_stat_pow_coeff

    print ('ExBig type '+str(type(bL.Ex5BigCluster))+' .')
    print ('ExLittle type '+str(type(bL.Ex5LittleCluster))+' .')

    # Wire up power models to the CPUs
    for cpu in root.system.descendants():
        if not isinstance(cpu, m5.objects.BaseCPU):
            continue
        cpu.power_state.default_state = "ON"
        if ('ex5_big' in str(type(cpu))) :
            cpu.power_model = CpuPowerModel(cpu.path(), big_dynamic_powcoeff, big_static_powcoeff)

        if ('ex5_LITTLE' in str(type(cpu))) :
            cpu.power_model = CpuPowerModel(cpu.path(), little_dynamic_powcoeff, little_static_powcoeff)

    bL.instantiate(options)

    # Dumping stats periodically
    # m5.stats.periodicStatDump(m5.ticks.fromSeconds(0.1e-3))
    bL.run()


if __name__ == "__m5_main__":
    main()
