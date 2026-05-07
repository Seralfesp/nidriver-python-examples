"""NI-DCPower Triggered DC Pulse Voltage with Measure Record.

This example uses an SMU which waits for a trigger from a DAQ card's counter output (at 10 Hz),
controlled by the DAQ card's Test Panel in NI-MAX.

Higher counter frequency might cause the buffer to overflow after some time passes.
Removing the plotting of matplotlib will help in avoiding this.

Further testing is required to improve the performance of this example.
"""
# Module imports
from math import floor

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as animation

import nidcpower


# Change the resource_name to the SMU name displayed in NI-MAX.
smu_resource_name = "PXI1Slot1"
smu_channel = "0"

# Change this according to the DAQ card you are using.
daq_resource_name = "PXI1Slot2"

voltage_points = []    # Voltage measurements will be stored here at the end for the voltage graph's Y-axis.
current_points = []    # Current measurements will be stored here at the end for the current graph's Y-axis.
x_time = []            # A delta time equal to the aperture time is used to determine the X-axis of the graphs.

plt.rcParams["figure.figsize"] = [7.50, 3.50]   # Set figure size for visualization.
plt.rcParams["figure.autolayout"] = True        # Set figure autolayout to True.

# Create figure and axes (voltage and time) objects.
fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(7, 9.6))

# SMU parameters.
pulse_level = 2.0
source_delay = 0
pulse_on_time = 200e-6
pulse_off_time = 50e-6
sample_rate = 1.8e6


def animate(i):
    """Animate and update plot constantly"""
    voltage_points = []
    current_points = []
    measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)
    for measure in measurements:
        voltage_points.append(measure[0])
        current_points.append(measure[1])

    volt_line.set_data(x_time, voltage_points)
    current_line.set_data(x_time, current_points)

    # print(session.fetch_backlog)  # You can uncomment this line if you want to keep an eye out on the measurement backlog

    return volt_line, current_line


# NI-DCPower Session.
with nidcpower.Session(resource_name=f"{smu_resource_name}/{smu_channel}") as session:
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.PULSE_VOLTAGE
    session.set_sequence(values=[pulse_level], source_delays=[source_delay])

    # Pulsing Settings
    session.pulse_voltage_level_range = abs(session.pulse_voltage_level)
    session.pulse_bias_voltage_level = 0.0
    session.pulse_current_limit = 1e-3
    session.pulse_current_limit_range = abs(session.pulse_current_limit)
    session.pulse_bias_current_limit = 1e-3
    session.pulse_on_time = pulse_on_time
    session.pulse_off_time = pulse_off_time
    session.pulse_bias_delay = 0

    session.source_delay = source_delay
    session.transient_response = nidcpower.TransientResponse.FAST
    session.aperture_time = 1 / sample_rate
    session.measure_record_length = 2
    session.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER

    actual_sample_rate = 1 / session.aperture_time

    session.measure_record_length = int(floor(actual_sample_rate * (pulse_on_time + pulse_off_time + 10e-6)))
    session.sequence_loop_count_is_finite = False
    session.measure_buffer_size = int(20e6)

    # Trigger Settings
    session.start_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
    session.digital_edge_start_trigger_input_terminal = f"/{daq_resource_name}/PFI12"
    session.sequence_advance_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
    session.digital_edge_sequence_advance_trigger_input_terminal = f"/{daq_resource_name}/PFI12"
    session.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE

    # This will automatically use the resource_name specified at the beginning of the NI-DCPower session.
    session.digital_edge_measure_trigger_input_terminal = f"/{smu_resource_name}/Engine{smu_channel}/SourceCompleteEvent"

    session.initiate()

    samples_acquired = 0

    measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)
    samples_acquired += len(measurements)

    # Formats aperture time for more readability.
    aperture_time = "{:.2e}".format(session.aperture_time)

    # Formats sample rate for more readability.
    sample_rate = "{:.2e}".format(1 / session.aperture_time)

    print(f"\nAperture Time: {aperture_time} seconds\nActual Sample Rate: {sample_rate} S/s")
    print("Size: ", len(measurements))

    # Prepare voltage and current points for plotting.
    for measure in measurements:
        voltage_points.append(measure[0])
        current_points.append(measure[1])

    print("Fetch Backlog: ", session.fetch_backlog)

    # x-axis of plots.
    x_time = [session.aperture_time * x for x in range(session.measure_record_length)]

    # Plot settings.

    # ax0 corresponds to the voltage graph.
    ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
    ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
    ax0.set_xlim(0, session.aperture_time*len(measurements))
    ax0.set_xlabel('Time (s)')
    ax0.set_ylabel('Voltage (V)')
    ax0.grid()
    volt_line, = ax0.plot(x_time, voltage_points)

    # ax1 corresponds to the current graph.
    ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
    ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
    ax1.set_xlim(0, session.aperture_time*len(measurements))
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Current (A)')
    ax1.grid()
    current_line, = ax1.plot(x_time, current_points)

    # FuncAnimation class which repeatedly calls the animate function to constantly update plot.
    ani = animation.FuncAnimation(fig, animate, interval=1, repeat=False, blit=True, cache_frame_data=False)

    plt.show()
