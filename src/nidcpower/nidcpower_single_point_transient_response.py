"""NI-DCPower Single Point - Transient Response Plot.

This example demonstrates how to plot the transient response
of an SMU while using Single Point Source Mode.

This example has been tested successfully with a PXIe-4139.
Active work is being done to test with other SMU models.
"""

# Module imports.
import time

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import nidcpower


# Variables.
voltage_level = 1
voltage_level_range = 6
aperture_time = 0
source_delay = 0
resource_name = "PXIe4145"

# Sets the amount of points to be captured in the measurement.
measure_record = 250

# Modify the Enum value in blue to either SLOW/NORMAL/FAST/CUSTOM depending on which response you would like to see.
transient_response = nidcpower.TransientResponse.NORMAL

# Constants.
voltage_points = []    # Voltage measurements will be stored here at the end for the voltage graph's Y-axis.
current_points = []    # Current measurements will be stored here at the end for the current graph's Y-axis.
x_time = []            # A delta time equal to the aperture time is used to determine the X-axis of the graph.

# Sets up graph properties:
plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True

# Creates graph subplot to be displayed:
fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(7, 9.6))

with nidcpower.Session(resource_name=resource_name, channels=0, reset=True, options={}, independent_channels=True) as session:
    # Common SMU settings
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level = voltage_level
    session.voltage_level_range = voltage_level_range

    # Below settings allow you to control the time it takes for the SMU to take a measurement.
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS

    # Longer aperture times to improve measurement resolution; shorter aperture times to increase the measurement speed.
    session.aperture_time = aperture_time

    # Determines when, in seconds, the SMU generates the Source Complete event,
    # potentially starting a measurement if the Measure When property is set to Automatically After Source Complete
    session.source_delay = source_delay
    
    # Below settings configure the transient response of the SMU.
    # Setting response to CUSTOM allows to fine tune the Gain BW, Compensation Frequency and Pole Zero Ratio.
    session.transient_response = transient_response
    """
    Gain Bandwidth: The frequency at which the unloaded loop gain extrapolates to 0 dB in the absence of additional poles and zeroes. Value range = 10 Hz to 20 MHz
    Compensation Frequency: The frequency at which a pole-zero pair is added to the system when the channel is in Constant Voltage mode. Value range = 20 Hz to 20 MHz
    Pole Zero Ratio: The ratio of the pole frequency to the zero frequency when the channel is in Constant Voltage/Current mode. Value range = 0.125 to 8.0

    Note: Do be careful about hardcoding custom transient settings. The default values for SLOW/NORMAL/FAST are voltage range/current range/device specific, so hardcoding would be helpful only when using 
    an identical device at the identical voltage/current ranges. It is recommended to use the default values, and if customization is necessary, to read back the values for each of the defaults and start from there.

    Uncomment the below settings if Transient Response is set to CUSTOM.
    """

    #session.voltage_gain_bandwidth = 5000
    #session.voltage_compensation_frequency = 50000
    #session.voltage_pole_zero_ratio = 0.16
    #session.current_gain_bandwidth = 40000
    #session.current_compensation_frequency = 250000
    #session.current_pole_zero_ratio = 4000

    # Below dictionary created for ease of showing the values in the output terminal.
    transient_settings = {
        "Voltage Gain Bandwidth": session.voltage_gain_bandwidth,
        "Voltage Compensation Frequency": session.voltage_compensation_frequency,
        "Voltage Pole Zero Ratio": session.voltage_pole_zero_ratio,
        "Current Gain Bandwidth": session.current_gain_bandwidth,
        "Current Compensation Frequency": session.current_compensation_frequency,
        "Current Pole Zero Ratio": session.current_pole_zero_ratio}

    # Set up a Measure Trigger to decouple the measure engine from the source engine,
    # enabling continuous measuring even when transitioning from one source point to the next

    # Starts measuring when the Measure Trigger signal is received.
    session.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER

    # Exports the Start Trigger generated after the session is initiated,
    # to activate the Measure Trigger. Measurement will start after session initiates.
    session.exported_start_trigger_output_terminal = f"/{resource_name}/PXI_Trig0"

    # Configures the Measure Trigger to wait for a Digital Edge (in this case the exported Start Trigger).
    session.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE

    # Configures the terminal where the instrument is expecting to receive the Measure Trigger (in this case the exported Start Trigger).
    session.digital_edge_measure_trigger_input_terminal = f"/{resource_name}/PXI_Trig0"

    # Other useful SMU settings.
    session.measure_record_length_is_finite = False

    # Sets a record length long enough to capture what you're insterested in.
    # You can play with this value to change the viewed graph.
    session.measure_record_length = measure_record
    session.measure_buffer_size = 20000000
    session.output_enabled = True

    # Initiate generation/acquisition.
    session.initiate()

    samples_acquired = 0
    
    start_time = time.time()    # SMU generation start time.
    measurements = session.channels[0].fetch_multiple(count=session.measure_record_length)
    samples_acquired += len(measurements)
    
    aperture_time = "{:.2e}".format(session.aperture_time)      # Formats aperture time for more readability.
    sample_rate = "{:.2e}".format(1 / session.aperture_time)    # Formats sample rate for more readability.
    
    end_time = time.time()  # SMU generation stop time.

    print(f"\nAperture Time: {aperture_time} seconds\nActual Sample Rate: {sample_rate} S/s")
    print(f"Generation Time: {end_time-start_time} seconds\nLoop Count: {samples_acquired}")
    print("Size: ", len(measurements))

    measure_dt = str(session.measure_record_delta_time).split(':')
    measure_dt = "{:e}".format(float(measure_dt[2]))

    print(f"Length: {session.measure_record_length}\nMeasure Delta Time: {measure_dt} seconds\nBacklog: {session.fetch_backlog}")
    print(transient_settings)

    # Stores voltage and current measurements in a new list for plotting purposes.
    for measure in measurements:
        voltage_points.append(measure[0])
        current_points.append(measure[1])
    
    x_time = [session.aperture_time * x for x in range(len(measurements))]

    # Plot settings.

    # ax0 corresponds to the voltage graph.
    ax0.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
    ax0.yaxis.set_major_formatter(ticker.EngFormatter(unit="V"))
    ax0.set_xlim(0, session.aperture_time*len(measurements))
    ax0.set_xlabel('Time (s)')
    ax0.set_ylabel('Voltage (V)')
    ax0.grid()
    ax0.plot(x_time, voltage_points)

    # ax1 corresponds to the current graph.
    ax1.xaxis.set_major_formatter(ticker.EngFormatter(unit="s"))
    ax1.yaxis.set_major_formatter(ticker.EngFormatter(unit="A"))
    ax1.set_xlim(0, session.aperture_time*len(measurements))
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Current (A)')
    ax1.grid()
    ax1.plot(x_time, current_points)

    # Formats title of the whole plot in relation to the Transient Response used.
    fig.suptitle(str(session.transient_response).title().lstrip("TransientResponse.") + " Response")

    plt.show()

    session.abort()
