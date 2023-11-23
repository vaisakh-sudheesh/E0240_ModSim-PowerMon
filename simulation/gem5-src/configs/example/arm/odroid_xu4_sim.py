import argparse
import os

import m5
from m5.objects import MathExprPowerModel, PowerModel

import fs_bigLITTLE as bL



bigcore_dvfsghz_table_volts = {
        '0.1'   : '0.9125',
        '0.2'   : '0.9125',
        '0.3'   : '0.9125',
        '0.4'   : '0.9125',
        '0.5'   : '0.9125',
        '0.6'   : '0.9125',
        '0.7'   : '0.9125',
        '0.8'   : '0.9375',
        '0.9'   : '0.9625',
        '1.0'   : '0.9875',
        '1.1'   : '1.0125',
        '1.2'   : '1.0375',
        '1.3'   : '1.0625',
        '1.4'   : '1.1125',
        '1.5'   : '1.1375',
        '1.6'   : '1.175',
        '1.7'   : '1.2125',
        '1.8'   : '1.25',
        '1.9'   : '1.25',
        '2.0'   : '1.25',
}

littlecore_dvfs_table_volts = {
        '0.2'   : '0.9375',
        '0.3'   : '0.9375',
        '0.4'   : '0.9375',
        '0.5'   : '0.9375',
        '0.6'   : '0.9375',
        '0.7'   : '0.975',
        '0.8'   : '1.025',
        '0.9'   : '1.0625',
        '1.0'   : '1.1125',
        '1.1'   : '1.11625',
        '1.2'   : '1.2125',
        '1.3'   : '1.275',
        '1.4'   : '1.275',
    }


class CpuPowerOn(MathExprPowerModel):
    def __init__(self, cpu_path, **kwargs):
        super(CpuPowerOn, self).__init__(**kwargs)
        # <x>A per IPC and then convert to Watt
        self.dyn = (
            "voltage * (1.000009 *  {}.ipc)".format(cpu_path)
        )
        self.st = (
            "voltage * (1.000020 * 0.001 * {}.ipc)".format(cpu_path)
        )


class CpuPowerOff(MathExprPowerModel):
    dyn = "0"
    st = "0"


class CpuPowerModel(PowerModel):
    def __init__(self, cpu_path, **kwargs):
        super(CpuPowerModel, self).__init__(**kwargs)
        self.pm = [
            CpuPowerOn(cpu_path),  # ON
            CpuPowerOff(),  # CLK_GATED
            CpuPowerOff(),  # SRAM_RETENTION
            CpuPowerOff(),  # OFF
        ]


def main():
    parser = argparse.ArgumentParser(
        description="ODroid-XU4 Power Model"
    )
    bL.addOptions(parser)
    options = parser.parse_args()

    if options.cpu_type != "exynos":
        m5.fatal("The power script requires 'exynos' CPUs type to be used.")

    root = bL.build(options)

    # Wire up power models to the CPUs
    for cpu in root.system.descendants():
        if not isinstance(cpu, m5.objects.BaseCPU):
            continue
        cpu.power_state.default_state = "ON"
        cpu.power_model = CpuPowerModel(cpu.path())

    bL.instantiate(options)

    # Dumping stats periodically
    # m5.stats.periodicStatDump(m5.ticks.fromSeconds(0.1e-3))
    bL.run()


if __name__ == "__m5_main__":
    main()
