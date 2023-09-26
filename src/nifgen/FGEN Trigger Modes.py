import time
import math
import keyboard

import nifgen

number_of_samples = 100

sine_wave = [math.sin(math.pi * 2 * x / (number_of_samples)) for x in range(number_of_samples)]
square_wave = [1.0 if x < (number_of_samples / 2) else -1.0 for x in range(number_of_samples)]
ramp_up = [x / (number_of_samples) for x in range(number_of_samples)]
ramp_down = [-1.0 * x for x in ramp_up]
sawtooth_wave = ramp_up[::2] + [(-1 + x) for x in ramp_up][::2]

with nifgen.Session(resource_name="C1_FGEN_S4", reset_device=True, options={}) as session:
    waveform_data = [sine_wave, square_wave, ramp_up, ramp_down, sawtooth_wave]
    waveform_handle = []
    session.output_mode = nifgen.OutputMode.SEQ
    session.arb_sample_rate = 1e6
    session.trigger_mode = nifgen.TriggerMode.BURST
    session.start_trigger_type = nifgen.StartTriggerType.SOFTWARE_EDGE
    for waveform in waveform_data:
        waveform_handle.append(session.create_waveform(waveform_data_array=waveform))
    sequence_handle = session.create_arb_sequence(waveform_handle, loop_counts_array=[1, 1, 1, 1, 1])
    session.configure_arb_sequence(sequence_handle=sequence_handle, gain=1.0, offset=0.0)

    try:
        session.initiate()
        print("Press the \'q\' key to send a software trigger to change waveforms. Press Ctrl + c to end the program")
        while True:
            if keyboard.is_pressed('q'):
                session.send_software_edge_trigger(trigger=nifgen.Trigger.START, trigger_id="")
                time.sleep(5.0)
    except KeyboardInterrupt:
        print("Program ended")