# E0240_ModSim-PowerMon

## Results Format

Results of a given workload is stored in to two files
- <workload-name>.prof - contains perf-stat command output which is sampled at an interval of 100ms
- <workload-name>.prof.powdata - corresponding Power measurements from SmartPower2 unit while the test load was running

### Interpreting prof.powdata file

In the test setup, the test device is connected to Channel-1 of SmartPower3 unit.
Hence the power data in CSV file can be found in column
- dev_ippwr-ch1-volts_mV: Voltage supplied to board at time sample in mV units
- dev_ippwr-ch1-ampere_mA: Current consumed by the board at time sample in mA units
- dev_ippwr-ch1-watt_mW: Power cosumed by the board at the time sample in mW units
- dev_ippwr-ch1-status_b: Status indicator that the channel is active/ON.

