import numpy as np
from devices.PIStage import PIStage
from devices.InfiniiumOscilloscope import InfiniiumOscilloscope, trig_mode_disct, acq_mode_dict

# Oscilloscope variables
channel="channel1"
autoscale=True
trigger_mode=trig_mode_disct[0]
trigger_level="330E-3"
save_setup=False
load_setup=False
setup_name="setup.set"
scale=0.1
offset=0.0
time_scale="200e-6"
time_position=0.0
acquire_mode=acq_mode_dict[0]
waveform_points=32000
name_csv="data/waveform_data"

# stage variables
bounds = [0, 25]
stage='M1121DG'
com_port='COM11'
baud_rate=9600


# port variables
port_oscilloscope = "USB0::0x0957::0x900A::MY51050155::INSTR"
port_stage = "COM11"

def acquisition(name):
    oscilloscope.single_acquisition(
    channel=channel, 
    autoscale=autoscale, 
    trigger_mode=trigger_mode, 
    trigger_level=trigger_level, 
    save_setup=save_setup, 
    load_setup=load_setup, 
    setup_name=setup_name, 
    scale=scale, 
    offset=offset,
    time_scale=time_scale,
    time_position=time_position,
    acquire_mode=acquire_mode,
    waveform_points=waveform_points
    )
    oscilloscope.get_waveform(
        channel=channel,
        name_csv= name + ".csv"
    )

# initialize oscilloscope
oscilloscope = InfiniiumOscilloscope(port_oscilloscope)
oscilloscope.initialize()
# initialize translation stage
stage = PIStage(bounds=bounds, stage=stage, com_port=port_stage, baud_rate=baud_rate)
stage.move_home()

position_array = np.linspace(0.0,10e-3,5)
final_position = position_array[0]

for i in range(len(position_array)):
    if(i == 0):
        final_position = stage.move(position_array[i])
    else:
        final_position = stage.move(position_array[i]-position_array[i-1])
    print(f"position : {final_position*1e2}")
    acquisition(name_csv + "_" + str(final_position*1e2))

oscilloscope.close()