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
    """
    Represents a connection to a Keysight Infiniium Oscilloscope and provides methods to control and retrieve data from the oscilloscope.
    """

    def __init__(self, address="TCPIP::169.254.66.192::INSTR"):
        """
        Initializes the oscilloscope connection using the provided VISA address.

        :param address: The VISA address of the oscilloscope.
        """
        self.address = address
        self.rm = pyvisa.ResourceManager()
        try:
            self.scope = self.rm.open_resource(self.address)
            self.scope.timeout = 20000  # Set command timeout
            self.scope.clear()  # Clear any existing errors or messages
            print("Connection to Infiniium Oscilloscope established.")
        except Exception as e:
            print(f"Failed to connect to Infiniium Oscilloscope: {e}")
            self.scope = None  # No connection if an error occurred

    def check_instrument_errors(self, command):
        """
        Queries the oscilloscope for any errors and prints them. Continues querying until no more errors are returned.

        :param command: The command after which to check for errors. Used for error reporting.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        while True:
            try:
                error_string = self.scope.query(":SYSTem:ERRor? STRing").strip()
                if error_string.startswith("+0,"):  # "No error"
                    break
                else:
                    print(f"ERROR: {error_string}, command: '{command}'")
            except Exception as e:
                print(f"Failed to check errors for command '{command}': {e}")
                break

    def do_command(self, command):
        """
        Sends a SCPI command to the oscilloscope and checks for errors.

        :param command: The SCPI command string to send to the oscilloscope.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        try:
            self.scope.write(command)
            self.check_instrument_errors(command)  # Check for errors related to the command
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")

    def do_command_ieee_block(self, command, values):
        """
        Sends a SCPI command along with binary data to the oscilloscope and checks for errors.

        :param command: The SCPI command to send.
        :param values: The binary data to send with the command.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return
        try:
            self.scope.write_binary_values(command, values, datatype='B')
            self.check_instrument_errors(command)  # Check for errors after sending the command
        except Exception as e:
            print(f"Failed to execute command '{command}': {e}")

    def do_query_string(self, query):
        """
        Sends a SCPI query to the oscilloscope, checks for errors, and returns the response as a string.

        :param query: The SCPI query string to send.
        :return: The response from the oscilloscope as a string.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query(query)
            self.check_instrument_errors(query)  # Check for errors related to the query
            return result
        except Exception as e:
            print(f"Failed to execute query '{query}': {e}")
            return None
        
    def do_query_number(self, query):
        """
        Sends a SCPI query to the oscilloscope, checks for errors, and returns the response as a floating-point number.

        :param query: The SCPI query string to send.
        :return: The response from the oscilloscope as a float.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query(query)
            self.check_instrument_errors(query)  # Check for errors related to the query
            return float(result)
        except Exception as e:
            print(f"Failed to execute query '{query}': {e}")
            return None

    def do_query_ieee_block(self, query):
        """
        Sends a SCPI query to the oscilloscope that expects a binary block response, checks for errors, and returns the binary data.

        :param query: The SCPI query string to send.
        :return: The binary data response from the oscilloscope.
        """
        if self.scope is None:
            print("Oscilloscope is not connected.")
            return None
        try:
            result = self.scope.query_binary_values(query, datatype='s', container=bytes)
            self.check_instrument_errors(query, exit_on_error=False)  # Check for errors, don't exit on error
            return result
        except Exception as e:
            print(f"Failed to execute IEEE block query '{query}': {e}")
            return None

    def initialize(self):
        """
        Initializes the oscilloscope by clearing any existing settings or errors and resetting the instrument to its default state.
        """
        self.do_command("*CLS")  # Clear the event status register
        idn_string = self.do_query_string("*IDN?")  # Query the instrument identification string
        print(f"Instrument ID: {idn_string}")
        self.do_command("*RST")  # Reset the instrument to its default settings

    def set_setup(self, channel, scale, offset, time_scale, time_position, acquire_mode):
        """
        Configures the oscilloscope's channel settings and acquisition parameters.

        :param channel: The oscilloscope channel to configure (e.g., "channel1").
        :param scale: The vertical scale (volts per division) for the specified channel.
        :param offset: The vertical offset for the specified channel.
        :param time_scale: The horizontal scale (seconds per division).
        :param time_position: The horizontal position (time offset).
        :param acquire_mode: The acquisition mode.
        """
        # Set the vertical scale and offset for the specified channel
        self.do_command(f":{channel}:SCALe {scale}")
        qresult = self.do_query_number(f":{channel}:SCALe?")
        print(f"{channel} vertical scale: {qresult}")

        self.do_command(f":{channel}:OFFSet {offset}")
        qresult = self.do_query_number(f":{channel}:OFFSet?")
        print(f"{channel} offset: {qresult}")

        # Set the horizontal scale and position
        self.do_command(f":TIMebase:SCALe {time_scale}")
        qresult = self.do_query_string(":TIMebase:SCALe?")
        print(f"Timebase scale: {qresult}")

        self.do_command(f":TIMebase:POSition {time_position}")
        qresult = self.do_query_string(":TIMebase:POSition?")
        print(f"Timebase position: {qresult}")

        # Set the acquisition mode
        self.do_command(f":ACQuire:MODE {acquire_mode}")
        qresult = self.do_query_string(":ACQuire:MODE?")
        print(f"Acquire mode: {qresult}")

    def save_setup(self, setup_name):
        """
        Saves the current oscilloscope setup to a file.

        :param setup_name: The name of the file to save the setup to.
        """
        setup_bytes = self.do_query_ieee_block(":SYSTem:SETup?")  # Query the oscilloscope setup
        with open(setup_name, "wb") as f:
            f.write(setup_bytes)  # Write the setup bytes to the specified file

    def load_setup(self, setup_name):
        """
        Loads an oscilloscope setup from a file.

        :param setup_name: The name of the file to load the setup from.
        """
        try:
            with open(setup_name, "rb") as f:
                setup_bytes = f.read()  # Read the setup bytes from the specified file
            self.do_command_ieee_block(":SYSTem:SETup", setup_bytes)  # Load the setup into the oscilloscope
            print("Setup bytes restored: %d" % len(setup_bytes))
        except Exception as e:
            print(f"Failed to load setup from '{setup_name}': {e}")

    def single_acquisition(self, 
                channel="channel1", 
                autoscale=True, 
                trigger_mode=trig_mode_disct[0], 
                trigger_level="330E-3", 
                save_setup=False, 
                load_setup=False, 
                setup_name="setup.set", 
                scale=0.1, 
                offset=0.0,
                time_scale="200e-6",
                time_position=0.0,
                acquire_mode=acq_mode_dict[0],
                waveform_points=32000
                ):
        """
        Configures the oscilloscope for a single acquisition based on provided settings and captures waveform data.

        :param channel: The oscilloscope channel to configure and acquire data from.
        :param autoscale: If True, uses the oscilloscope's auto-scale feature to automatically adjust settings.
        :param trigger_mode: The trigger mode to use for acquisition.
        :param trigger_level: The voltage level to set for the trigger.
        :param save_setup: If True, saves the current oscilloscope setup to a file.
        :param load_setup: If True, loads oscilloscope settings from a previously saved setup file.
        :param setup_name: The file name to save or load the oscilloscope setup.
        :param scale: The vertical scale (volts per division) for the specified channel.
        :param offset: The vertical offset for the specified channel.
        :param time_scale: The horizontal scale (seconds per division).
        :param time_position: The horizontal position (time offset from the trigger point).
        :param acquire_mode: The acquisition mode for the oscilloscope.
        :param waveform_points: The number of waveform points to capture.
        """
        try:
            # Set the probe attenuation factor to 1x for the specified channel
            self.do_command(f":{channel}:PROBe 1.0")
            qresult = self.do_query_string(f":{channel}:PROBe?")
            print(f"{channel} probe attenuation factor: {qresult}")

            # Automatically adjust the oscilloscope settings for optimal viewing, if autoscale is enabled
            if autoscale:
                print("Autoscale.")
                self.do_command(":AUToscale")

            # Configure the trigger settings based on the specified mode and parameters
            self.do_command(f":TRIGger:MODE {trigger_mode}")
            qresult = self.do_query_string(":TRIGger:MODE?")
            print(f"Trigger mode: {qresult}")

            # If the trigger mode is EDGE, set additional EDGE trigger parameters
            if trigger_mode == "EDGE":
                self.do_command(f":TRIGger:EDGE:SOURce {channel}")
                qresult = self.do_query_string(":TRIGger:EDGE:SOURce?")
                print(f"Trigger edge source: {qresult}")
                self.do_command(f":TRIGger:LEVel {channel},{trigger_level}")
                qresult = self.do_query_string(f":TRIGger:LEVel? {channel}")
                print(f"Trigger level, {channel}: {qresult}")
                self.do_command(":TRIGger:EDGE:SLOPe POSitive")
                qresult = self.do_query_string(":TRIGger:EDGE:SLOPe?")
                print(f"Trigger edge slope: {qresult}")

            # Save the current oscilloscope setup to a file, if requested
            if save_setup:
                self.save_setup(setup_name)
                print(f"Oscilloscope setup saved to {setup_name}.")

            # Load a previously saved oscilloscope setup from a file, if requested
            if load_setup:
                self.load_setup(setup_name)
                print(f"Oscilloscope setup loaded from {setup_name}.")

            # If not loading from a file, manually configure the oscilloscope settings
            if not load_setup:
                self.set_setup(channel, scale, offset, time_scale, time_position, acquire_mode)

            # Configure the number of waveform points to capture and initiate a single acquisition
            self.do_command(f":ACQuire:POINts {waveform_points}")
            self.do_command(":DIGitize")
            print("Single acquisition completed.")

        except Exception as e:
            print(f"Error during single acquisition: {e}")


    def make_measures(self, channel):
        """
        Performs frequency and amplitude measurements on the specified channel of the oscilloscope.

        :param channel: The oscilloscope channel (e.g., "channel1") on which to perform measurements.
        """
        try:
            # Set the measurement source to the specified channel
            self.do_command(f":MEASure:SOURce {channel}")
            # Confirm the measurement source
            qresult = self.do_query_string(":MEASure:SOURce?")
            print(f"Measure source: {qresult}")

            # Perform and print frequency measurement
            self.do_command(":MEASure:FREQuency")
            qresult = self.do_query_string(":MEASure:FREQuency?")
            print(f"Measured frequency on {channel}: {qresult}")

            # Perform and print amplitude measurement
            self.do_command(":MEASure:VAMPlitude")
            qresult = self.do_query_string(":MEASure:VAMPlitude?")
            print(f"Measured vertical amplitude on {channel}: {qresult}")

        except Exception as e:
            print(f"Error during measurements on {channel}: {e}")

    def get_image(self, image_name):
        """
        Downloads the current screen image from the oscilloscope and saves it to a file.

        :param image_name: The file name (including path, if necessary) where the screen image will be saved.
        """
        try:
            # Request the screen image in PNG format
            screen_bytes = self.do_query_ieee_block(":DISPlay:DATA? PNG")
            if screen_bytes is not None:
                # Save the image bytes to the specified file
                with open(image_name, "wb") as f:
                    f.write(screen_bytes)
                print(f"Screen image written to {image_name}.")
            else:
                print("Failed to retrieve screen image.")

        except Exception as e:
            print(f"Error occurred while getting the screen image: {e}")



    def get_preamble(self):
        """
        Retrieves and prints the preamble information from the oscilloscope, which includes various waveform settings and parameters. 
        Also, it extracts numeric values for some of these parameters for potential later use in calculations.

        :return: A tuple containing important numeric values extracted from the preamble, including x_increment, x_origin, x_units, y_increment, y_origin, and y_units. If the preamble cannot be retrieved, None is returned.
        """
        try:
            # Query the oscilloscope for the preamble string that contains metadata about the waveform
            preamble_string = self.do_query_string(":WAVeform:PREamble?")
            if preamble_string:
                # Split the preamble string into its constituent parts
                (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin, x_reference, y_increment, y_origin, 
                y_reference, coupling, x_display_range, x_display_origin, y_display_range, y_display_origin, 
                date, time, frame_model, acq_mode, completion, x_units, y_units, max_bw_limit, min_bw_limit) = preamble_string.split(",")

                # Print out the extracted preamble information for user reference
                print("Waveform format: %s" % wav_form_dict[int(wav_form)])
                print("Acquire type: %s" % acq_type_dict[int(acq_type)])
                print("Waveform points desired: %s" % wfmpts)
                print("Waveform average count: %s" % avgcnt)
                print("Waveform X increment: %s" % x_increment)
                print("Waveform X origin: %s" % x_origin)
                print("Waveform Y increment: %s" % y_increment)
                print("Waveform Y origin: %s" % y_origin)
                print("Coupling: %s" % coupling_dict[int(coupling)])
                print("Waveform X display range: %s" % x_display_range)
                print("Waveform Y display range: %s" % y_display_range)
                print("Date: %s" % date)
                print("Time: %s" % time)
                print("Acquire mode: %s" % acq_mode_dict[int(acq_mode)])
                print("Waveform X units: %s" % units_dict[int(x_units)])
                print("Waveform Y units: %s" % units_dict[int(y_units)])

                # Query the oscilloscope for specific numeric values related to the waveform that may be used in later calculations
                x_increment = self.do_query_number(":WAVeform:XINCrement?")
                x_origin = self.do_query_number(":WAVeform:XORigin?")
                y_increment = self.do_query_number(":WAVeform:YINCrement?")
                y_origin = self.do_query_number(":WAVeform:YORigin?")

                # Return the extracted numeric values
                return x_increment, x_origin, units_dict[int(x_units)], y_increment, y_origin, units_dict[int(y_units)], date, time
            else:
                print("Failed to retrieve the preamble string.")
                return None
        except Exception as e:
            print(f"Error occurred while getting the preamble: {e}")
            return None


def get_waveform(self, channel="channel1", waveform_format=wav_form_dict[1], name_csv="waveform_data.csv"):
    """
    Retrieves waveform data from the specified oscilloscope channel and saves it to a CSV file.

    :param channel: The channel from which to retrieve waveform data (e.g., "channel1").
    :param waveform_format: The format of the waveform data to be retrieved.
    :param name_csv: The name of the CSV file where the waveform data will be saved.
    """
    try:
        # Query the oscilloscope for the current waveform type and print it
        qresult = self.do_query_string(":WAVeform:TYPE?")
        print(f"Waveform type: {qresult}")

        # Query the oscilloscope for the number of waveform points and print it
        qresult = self.do_query_string(":WAVeform:POINts?")
        print(f"Waveform points: {qresult}")

        # Set the source of the waveform data to the specified channel
        self.do_command(f":WAVeform:SOURce {channel}")
        # Confirm the waveform source and print it
        qresult = self.do_query_string(":WAVeform:SOURce?")
        print(f"Waveform source: {qresult}")

        # Set the format of the waveform data to be retrieved
        self.do_command(f":WAVeform:FORMat {waveform_format}")
        # Confirm the waveform format and print it
        print(f"Waveform format: {self.do_query_string(':WAVeform:FORMat?')}")

        # Retrieve and print the preamble information, which includes scaling factors and units
        x_increment, x_origin, x_units, y_increment, y_origin, y_units, date, time = self.get_preamble()
        
        # Disable streaming to retrieve the waveform data
        self.do_command(":WAVeform:STReaming OFF")
        # Query the oscilloscope for the waveform data
        sData = self.do_query_ieee_block(":WAVeform:DATA?")
        # Unpack the retrieved waveform data
        values = struct.unpack("%db" % len(sData), sData)
        print(f"Number of data values: {len(values)}")

        # Write the waveform data, along with scaling factors and units, to the specified CSV file
        with open(name_csv, "w") as f:
            f.write("Date, Time, Time (s), Voltage (V)\n")
            for i in range(len(values)):
                time_val = x_origin + (i * x_increment)
                voltage = (values[i] * y_increment) + y_origin
                f.write(f"{date}, {time}, {time_val:E}, {voltage:f}\n")
        print(f"Waveform data written to {name_csv}.")

    except Exception as e:
        print(f"Error occurred while getting the waveform: {e}")

def close(self):
    """
    Closes the connection to the oscilloscope.
    """
    if self.scope is not None:
        self.scope.close()  # Close the VISA resource
        print("Connection to Infiniium Oscilloscope closed.")

