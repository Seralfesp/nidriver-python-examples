"""NI-DCPower Hardware-Timed Two-Channel Voltage Sweep (IV Curve).

This example demonstrates how to set up a hardware-timed,
two-channel nested voltage sweep and display the results in a graph (IV Curve).

Use this example to produce the characteristic curves of a FET transistor.
It can be easily adapted to test a BJT by performing a current sweep instead of a voltage sweep.
This example performs a hardware-timed sweep (with triggers and events) using Sequence source mode.

When the code is run and the graph displays,
you can click on each plot in the right hand corner of the graph to enable/disable its visibility.
"""

# Module imports
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import nidcpower


gate_resource_name = "PXI1Slot1"
gate_channel = "0"
drain_resource_name = "PXI1Slot2"
drain_channel = "0"

gain_voltage_start = 3.5
gain_voltage_stop = 3.9

drain_voltage_start = 1
drain_voltage_stop = 5

# Number of plots to be displayed on the graph, also used for the voltages of the gate channel
plots = 5
# Limits the plots variable to a minimum of 1, in case a value less than 1 is specified
plots = np.clip(plots, 1, 2147483647)
# Number of measurements to be taken by the drain channel
points = 10
# Limits the points variable to a minimum of 1, in case a value less than 1 is specified
points = np.clip(points, 1, 2147483647)

gate_sequence = []
drain_sequence = []
source_delays = []

# Generates step voltages for the gate channel and drain channel SMU:
if plots - 1 == 0:
    gate_sequence.append(gain_voltage_start)

elif points - 1 == 0:
    drain_sequence.append(drain_voltage_start)

else:
    voltages_0 = (gain_voltage_stop - gain_voltage_start) / (plots - 1)
    for i in range(plots):
        gate_sequence.append((voltages_0 * i) + gain_voltage_start)

    voltages_1 = (drain_voltage_stop - drain_voltage_start) / (points - 1)
    for i in range(points):
        drain_sequence.append((voltages_1 * i) + drain_voltage_start)


# Sets up graph properties:
plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True

# Creates graph subplot to be displayed:
fig, ax = plt.subplots(nrows=1, figsize=(7, 9.6))

# Initializes both SMU sessions:
with nidcpower.Session(resource_name=f"{gate_resource_name}/{gate_channel}", options={}) as gate_session, nidcpower.Session(resource_name=f"{drain_resource_name}/{drain_channel}", options={}) as drain_session:
    # Settings for the gate channel:
    gate_session.source_mode = nidcpower.SourceMode.SEQUENCE
    gate_session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    gate_session.voltage_level_autorange = True
    gate_session.current_limit_autorange = True
    gate_session.source_delay = 0.003
    gate_session.current_limit = 0.01
    
    # Creates an array source delays of the same size as the step voltages to configure the set_sequence method for the gate channel:
    for i in range(len(gate_sequence)):
        source_delays.append(0.003)

    gate_session.set_sequence(values=gate_sequence, source_delays=source_delays)

    # Triggering setup of the gate channel:
    gate_session.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
    gate_session.digital_edge_source_trigger_input_terminal = f"/{drain_resource_name}/Engine{drain_channel}/SequenceIterationCompleteEvent"

    gate_session.commit()

    # Settings for the drain channel:
    drain_session.source_mode = nidcpower.SourceMode.SEQUENCE
    drain_session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    drain_session.voltage_level_autorange = True
    drain_session.current_limit_autorange = True
    drain_session.source_delay = 0.005
    drain_session.current_limit = 0.01

    # Resets the previous source_delays array,
    # and creates a new array source delays of the same size as the step voltages,
    # to configure the set_sequence method for the drain channel:
    source_delays = []
    for i in range(len(drain_sequence)):
        source_delays.append(0.005)

    drain_session.set_sequence(values=drain_sequence, source_delays=source_delays)

    # Triggering setup of the drain channel:
    drain_session.start_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
    drain_session.digital_edge_start_trigger_input_terminal = f"/{gate_resource_name}/Engine{gate_channel}/MeasureCompleteEvent"
    drain_session.sequence_advance_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
    drain_session.digital_edge_sequence_advance_trigger_input_terminal = f"/{gate_resource_name}/Engine{gate_channel}/MeasureCompleteEvent"

    drain_session.sequence_loop_count = plots
    drain_session.commit()

    # Initiates both SMU sessions:
    drain_session.initiate()
    gate_session.initiate()

    drain_session.wait_for_event(event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=15)

    # Stores measurements of the gate channel::
    gate_measurements = gate_session.fetch_multiple(count=plots, timeout=10)

    # Creates an array to store measurements of the drain channel:
    drain_measurements = []
    for plot in range(len(gate_measurements)):
        drain_measurements.append(drain_session.fetch_multiple(count=points, timeout=10))

    # Voltage and current arrays of the drain channel measurements to later use each pair as a plot:
    drain_voltages = []
    drain_currents = []

    # Formatting for better output visualization:
    line_format = '{:<18} {:<18} {:<18}'
    print(line_format.format('Gate Voltage (V)', 'Drain Current (A)',  'Drain Voltage (V)'))

    for plot in range(len(gate_measurements)):
        for point in range(len(drain_measurements[0])):
            drain_voltages.append(drain_measurements[plot][point].voltage)
            drain_currents.append(drain_measurements[plot][point].current)
            print(line_format.format("{:.3f}".format(gate_measurements[plot][0]),
                                     "{:.3e}".format(drain_measurements[plot][point].current),
                                     "{:.3f}".format(drain_measurements[plot][point].voltage)))

        # Plots a set of points where xaxis = Voltages and yaxis = Currents of the drain channel for each gate voltage, and adds a legend with the corresponding gate voltage value:
        ax.plot(drain_voltages, drain_currents, marker='o', label=f"{gate_measurements[plot].voltage:3f} V")
        drain_voltages = []
        drain_currents = []

    # Disables generation/acquisition on both SMUs:
    gate_session.output_enabled = False
    drain_session.output_enabled = False

    # Settings for the plot to be displayed:
    graphs = {}

    lines = ax.get_lines()
    leg = ax.legend(fancybox=True, shadow=True)
    lined = {}  # Will map legend lines to original lines.
    for legline, origline in zip(leg.get_lines(), lines):
        legline.set_picker(True)    # # Enable picking on the legend line.
        legline.set_pickradius(3)
        lined[legline] = origline
    
    def on_pick(event):
        """On the pick event, find the original line corresponding to the legend proxy line, and toggle its visibility."""
        legline = event.artist
        origline = lined[legline]
        visible = not origline.get_visible()
        origline.set_visible(visible)
        #Change the alpha on the line in the legend so we can see what lines
        #that have been toggled.
        legline.set_alpha(1.0 if visible else 0.2)
        fig.canvas.draw()

    # Graph settings:
    ax.xaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
    ax.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (A)')
    ax.grid()

    # Connects 'pick_event' to on_pick function to hide and display each plot by clicking on their corresponding legend color:
    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.suptitle("Current (Amps) vs Voltage (Volts)")

    plt.show()
