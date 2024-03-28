import pyvisa
import struct

trig_mode_disct = {
    0: "EDGE",
    1: "GLITCH",
    2: "PATTERN",
    3: "STATE",
    4: "DELAY",
    5: "TIMEOUT",
    6: "TV",
    7: "COMM",
    8: "RUNT",
    9: "SEQUENCE",
    10: "SHOLD",
    11: "TRANSITION",
    12: "WINDOW",
    13: "PWIDth",
    14: "ADVANCED",
    15: "SBUS<N>"  # Assuming 'SBUS<N>' is a placeholder for something like 'SBUS1', 'SBUS2', etc.
}

wav_form_dict = {
    0 : "ASCii",
    1 : "BYTE",
    2 : "WORD",
    3 : "LONG",
    4 : "LONGLONG",
}
acq_type_dict = {
    1 : "RAW",
    2 : "AVERage",
    3 : "VHIStogram",
    4 : "HHIStogram",
    6 : "INTerpolate",
    10 : "PDETect",
}
acq_mode_dict = {
    0 : "RTIMe",
    1 : "ETIMe",
    3 : "PDETect",
}
coupling_dict = {
    0 : "AC",
    1 : "DC",
    2 : "DCFIFTY",
    3 : "LFREJECT",
}
units_dict = {
    0 : "UNKNOWN",
    1 : "VOLT",
    2 : "SECOND",
    3 : "CONSTANT",
    4 : "AMP",
    5 : "DECIBEL",
}

class InfiniiumOscilloscope:
    def __init__(self, address="TCPIP::169.254.66.192::INSTR"):
        self.address = address
        self.rm = pyvisa.ResourceManager()
        try:
            self.scope = self.rm.open_resource(self.address)
            self.scope.timeout = 20000
            self.scope.clear()
            print("Connection to Infiniium Oscilloscope established.")
        except Exception as e:
            print(f"Failed to connect to Infiniium Oscilloscope: {e}")
            self.scope = None

    def check_instrument_errors(self, command):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        while True:
            try:
                error_string = self.scope.query(":SYSTem:ERRor? STRing").strip()
                if error_string:  # If there is an error string value.
                    if error_string.startswith("+0,"):  # "No error"
                        break
                    else:
                        print(f"ERROR: {error_string}, command: '{command}'")
            except Exception as e:
                print(f"Failed to check errors for command '{command}': {e}")
                break

    def do_command(self, command):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        try:
            self.scope.write(command)
            self.check_instrument_errors(command)
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")

    def do_command_ieee_block(self, command, values):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        try:
            self.scope.write_binary_values(command, values, datatype='B')
            self.check_instrument_errors(command)
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")

    def do_query_string(self, query):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query(query)
            self.check_instrument_errors(query)
            return result
        except Exception as e:
            print(f"Failed to execute query '{query}': {e}")
            return None
        
    def do_query_number(self, query):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query(query)
            self.check_instrument_errors(query)
            return float(result)
        except Exception as e:
            print(f"Failed to execute query '{query}': {e}")
            return None

    def do_query_ieee_block(self, query):
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query_binary_values(query, datatype='s', container=bytes)
            self.check_instrument_errors(query, exit_on_error=False)
            return result
        except Exception as e:
            print(f"Failed to execute IEEE block query '{query}': {e}")
            return None

    def initialize(self):
        self.do_command("*CLS")
        idn_string = self.do_query_string("*IDN?")
        print(f"Instrument ID: {idn_string}")
        self.do_command("*RST")

    def set_setup(self, channel, scale, offset, time_scale, time_position, acquire_mode):
        self.do_command(f":{channel}:SCALe {scale}")
        qresult = self.do_query_number(f":{channel}:SCALe?")
        print(f"{channel} vertical scale: {qresult}")
        self.do_command(f":{channel}:OFFSet {offset}")
        qresult = self.do_query_number(f":{channel}:OFFSet?")
        print(f"{channel} offset: {qresult}")
        self.do_command(f":TIMebase:SCALe {time_scale}")
        qresult = self.do_query_string(":TIMebase:SCALe?")
        print(f"Timebase scale: {qresult}")
        self.do_command(f":TIMebase:POSition {time_position}")
        qresult = self.do_query_string(":TIMebase:POSition?")
        print(f"Timebase position: {qresult}")
        self.do_command(f":ACQuire:MODE {acquire_mode}")
        qresult = self.do_query_string(":ACQuire:MODE?")
        print(f"Acquire mode: {qresult}")

    def save_setup(self, setup_name):
        setup_bytes = self.do_query_ieee_block(":SYSTem:SETup?")
        with open(setup_name, "wb") as f:
            f.write(setup_bytes)

    def load_setup(self, setup_name):
        try:
            with open(setup_name, "rb") as f:
                setup_bytes = f.read()
            self.do_command_ieee_block(":SYSTem:SETup", setup_bytes)
            print("Setup bytes restored: %d" % len(setup_bytes))
        except Exception as e:
            print(f"Failed to load setup from '{setup_name}': {e}")

    def single_acquisition(self, 
                channel="channel1", 
                autoscale=True, 
                trigger_mode=trig_mode_disct[0], 
                trigger_level="330E-3", 
                save_setup=False, load_setup=False, 
                setup_name="setup.set", 
                scale=0.1, 
                offset=0.0,
                time_scale="200e-6",
                time_position=0.0,
                acquire_mode = acq_mode_dict[0],
                waveform_points=32000
                ):
        try:
            # Set probe attenuation factor to x1
            self.do_command(f":{channel}:PROBe 1.0")
            qresult = self.do_query_string(f":{channel}:PROBe?")
            print(f"{channel} probe attenuation factor: {qresult}")

            # Use auto-scale to automatically set up oscilloscope.
            if(autoscale):
                print("Autoscale.")
                self.do_command(":AUToscale")

            # Set trigger mode.
            self.do_command(f":TRIGger:MODE {trigger_mode}")
            qresult = self.do_query_string(":TRIGger:MODE?")
            print("Trigger mode: %s" % qresult)

            if(trigger_mode == "EDGE"):
                # Set EDGE trigger parameters.
                self.do_command(f":TRIGger:EDGE:SOURce {channel}")
                qresult = self.do_query_string(":TRIGger:EDGE:SOURce?")
                print(f"Trigger edge source: {qresult}")
                self.do_command(f":TRIGger:LEVel {channel},{trigger_level}")
                qresult = self.do_query_string(f":TRIGger:LEVel? {channel}")
                print(f"Trigger level, {channel}: {qresult}")
                self.do_command(":TRIGger:EDGE:SLOPe POSitive")
                qresult = self.do_query_string(":TRIGger:EDGE:SLOPe?")
                print("Trigger edge slope: %s" % qresult)

            # Save oscilloscope setup.
            if(save_setup):
                save_setup(setup_name)
                print(f"Oscilloscope setup saved to {setup_name}.")

            if(not load_setup):
                # Change oscilloscope settings with individual commands
                self.set_setup(channel, scale, offset, time_scale, time_position, acquire_mode)
            else:
                # Set up oscilloscope by loading a previously saved setup
                load_setup(setup_name)
                print(f"Oscilloscope setup loaded from {setup_name}.")

            # Set the desired number of waveform points,
            # and capture a single acquisition.
            self.do_command(f":ACQuire:POINts {waveform_points}")
            self.do_command(":DIGitize")
            print("Single acquisition completed.")

        except Exception as e:
            print(f"Error during single acquisition: {e}")

    def make_measures(self, channel):
        try:
            # Make measurements.
            self.do_command(f":MEASure:SOURce {channel}")
            qresult = self.do_query_string(":MEASure:SOURce?")
            print(f"Measure source: {qresult}")
            self.do_command(":MEASure:FREQuency")
            qresult = self.do_query_string(":MEASure:FREQuency?")
            print(f"Measured frequency on {channel}: {qresult}")
            self.do_command(":MEASure:VAMPlitude")
            qresult = self.do_query_string(":MEASure:VAMPlitude?")
            print(f"Measured vertical amplitude on {channel}: {qresult}")

        except Exception as e:
            print(f"Error during measurements on {channel}: {e}")

    def get_image(self, image_name):
        try:
            # Download the screen image
            screen_bytes = self.do_query_ieee_block(":DISPlay:DATA? PNG")
            if screen_bytes is not None:
                # Save display data values to file using a context manager
                with open(image_name, "wb") as f:
                    f.write(screen_bytes)
                print(f"Screen image written to {image_name}.")
            else:
                print("Failed to retrieve screen image.")
        except Exception as e:
            print(f"Error occurred while getting the screen image: {e}")


    def get_preamble(self):
        try:
            preamble_string = self.do_query_string(":WAVeform:PREamble?")
            if preamble_string:
                # Unpack the preamble string into individual variables
                (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin, x_reference, y_increment, y_origin, 
                y_reference, coupling, x_display_range, x_display_origin, y_display_range, y_display_origin, 
                date, time, frame_model, acq_mode, completion, x_units, y_units, max_bw_limit, min_bw_limit) = preamble_string.split(",")

                print("Waveform format: %s" % wav_form_dict[int(wav_form)])
                print("Acquire type: %s" % acq_type_dict[int(acq_type)])
                print("Waveform points desired: %s" % wfmpts)
                print("Waveform average count: %s" % avgcnt)
                print("Waveform X increment: %s" % x_increment)
                print("Waveform X origin: %s" % x_origin)
                print("Waveform X reference: %s" % x_reference) # Always 0.
                print("Waveform Y increment: %s" % y_increment)
                print("Waveform Y origin: %s" % y_origin)
                print("Waveform Y reference: %s" % y_reference) # Always 0.
                print("Coupling: %s" % coupling_dict[int(coupling)])
                print("Waveform X display range: %s" % x_display_range)
                print("Waveform X display origin: %s" % x_display_origin)
                print("Waveform Y display range: %s" % y_display_range)
                print("Waveform Y display origin: %s" % y_display_origin)
                print("Date: %s" % date)
                print("Time: %s" % time)
                print("Frame model #: %s" % frame_model)
                print("Acquire mode: %s" % acq_mode_dict[int(acq_mode)])
                print("Completion pct: %s" % completion)
                print("Waveform X units: %s" % units_dict[int(x_units)])
                print("Waveform Y units: %s" % units_dict[int(y_units)])
                print("Max BW limit: %s" % max_bw_limit)
                print("Min BW limit: %s" % min_bw_limit)

                # Get numeric values for later calculations.
                x_increment = self.do_query_number(":WAVeform:XINCrement?")
                x_origin = self.do_query_number(":WAVeform:XORigin?")
                y_increment = self.do_query_number(":WAVeform:YINCrement?")
                y_origin = self.do_query_number(":WAVeform:YORigin?")

                return x_increment, x_origin, units_dict[int(x_units)], y_increment, y_origin, units_dict[int(y_units)], date, time
            
            else:
                print("Failed to retrieve the preamble string.")
                return None
        except Exception as e:
            print(f"Error occurred while getting the preamble: {e}")
            return None

    def get_waveform(
            self,
            channel="channel1", 
            waveform_format=wav_form_dict[1],
            name_csv="waveform_data.csv"
            ):
        try:
            # Download waveform data.
            # Get the waveform type.
            qresult = self.do_query_string(":WAVeform:TYPE?")
            print(f"Waveform type: {qresult}")
            # Get the number of waveform points.
            qresult = self.do_query_string(":WAVeform:POINts?")
            print(f"Waveform points: {qresult}")
            # Set the waveform source.
            self.do_command(f":WAVeform:SOURce {channel}")
            qresult = self.do_query_string(":WAVeform:SOURce?")
            print(f"Waveform source: {qresult}")
            # Choose the format of the data returned:
            self.do_command(f":WAVeform:FORMat {waveform_format}")
            print(f"Waveform format: {self.do_query_string(":WAVeform:FORMat?")}")

            x_increment, x_origin, x_units, y_increment, y_origin, y_units, date, time = self.get_preamble()
            
            # Get the waveform data.
            self.do_command(":WAVeform:STReaming OFF")
            sData = self.do_query_ieee_block(":WAVeform:DATA?")
            # Unpack signed byte data.
            values = struct.unpack("%db" % len(sData), sData)
            print("Number of data values: %d" % len(values))
            # Save waveform data values to CSV file.
            with open(name_csv, "w") as f:
                f.write("%s, %s\n" % ("date", date))
                f.write("%s, %s\n" % ("time", time))
                f.write("%s, %s\n" % ("x units", x_units))
                f.write("%s, %s\n" % ("y units", y_units))
                for i in range(0, len(values) - 1):
                    time_val = x_origin + (i * x_increment)
                    voltage = (values[i] * y_increment) + y_origin
                    f.write("%E, %f\n" % (time_val, voltage))
            print(f"Waveform format BYTE data written to {name_csv}.")

        except Exception as e:
            print(f"Error occurred while getting the waveform: {e}")

    def close(self):
        if self.scope is not None:
            self.scope.close()
            print("Connection to Infiniium Oscilloscope closed.")
