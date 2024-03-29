from .mmc_wrapper import MMC_Wrapper
from qtpy.QtCore import QThread

class PIStage:
    """
    A class to control and manage movements of a Physik Instrumente (PI) stage using the MMC protocol.

    Attributes:
        bounds (list): The minimum and maximum allowable positions of the stage.
        stage (str): The model of the stage being used.
        com_port (str): The COM port to which the stage is connected.
        baud_rate (int): The baud rate for the serial communication.
        wrapper (MMC_Wrapper): An instance of the MMC_Wrapper to interface with the stage.
        axis (int): The currently selected axis of the stage.

    Methods:
        init_stage(): Initializes the stage by setting up the serial connection and selecting the first device.
        enumerate_devices(wrapper): Enumerates the connected PI devices.
        move_home(): Moves the stage to its home position.
        close(): Closes the serial connection to the stage.
        stop_motion(): Stops any ongoing movement of the stage.
        move(position): Moves the stage to a specified position.
        is_moving(threshold): Checks if the stage is currently moving.
    """
    
    _controller_units = 'mm'  # Default units, update accordingly if needed
    
    def __init__(self, bounds=[0, 25], stage='M1121DG', com_port='COM11', baud_rate=9600):
        """
        Initializes the PIStage class with specified bounds, stage model, COM port, and baud rate.
        Also initializes the stage by setting up the serial connection and selecting the first device.
        """
        self.bounds = bounds
        self.stage = stage
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.wrapper = None
        self.axis = None
        self.init_stage()

    def init_stage(self):
        """
        Initializes the stage by setting up the serial connection and selecting the first device.
        It attempts to open the serial connection and enumerate the connected devices.
        If successful, selects the first device as the current axis and prints its initial position.
        """
        try:
            self.wrapper = MMC_Wrapper(self.stage, self.com_port, self.baud_rate)
            self.wrapper.open()
            devices = self.enumerate_devices(self.wrapper)
            if devices:
                self.axis = devices[0]
                self.wrapper.MMC_select(self.axis)
                pos = self.wrapper.getPos()
                print(f"Initialization Success - Device: {devices[0]}, Position: {pos}")
            else:
                print("No devices found.")
        except Exception as e:
            print(f"Initialization failed: {e}")

    def enumerate_devices(self, wrapper):
        """
        Enumerates the connected PI devices.

        Parameters:
            wrapper (MMC_Wrapper): An instance of the MMC_Wrapper used to interface with the devices.

        Returns:
            list: A list of integers representing the connected devices.
        """
        try:
            devices = wrapper.MMC_initNetwork(3)  # The number can be adjusted based on the expected number of connected devices
            return devices
        except Exception as e:
            print(f"Error enumerating devices: {e}")
            return []

    def move_home(self):
        """
        Moves the stage to its home position. It continuously checks the stage's position to determine
        when the homing process has completed.
        """
        if not self.wrapper:
            print("Stage not initialized.")
            return

        try:
            self.wrapper.find_home()
            print("Homing started...")
            while self.is_moving():
                QThread.msleep(100)  # Short delay between checks
            print("Homing complete.")
            self.wrapper.MMC_sendCommand('DH')  # Define the current position as home
            QThread.msleep(500)  # Short delay to ensure the command is processed
            pos = self.wrapper.getPos()
            print(f"Final position: {pos}")
        except Exception as e:
            print(f"Error moving home: {e}")

    def close(self):
        """
        Closes the serial connection to the stage.
        """
        if self.wrapper:
            try:
                self.wrapper.MMC_COM_close()
                print("Connection closed successfully.")
            except Exception as e:
                print(f"Error closing connection: {e}")

    def stop_motion(self):
        """
        Stops any ongoing movement of the stage.
        """
        if self.wrapper:
            try:
                self.wrapper.MMC_globalBreak()
                print("Motion stopped.")
            except Exception as e:
                print(f"Error stopping motion: {e}")

    def move(self, position):
        """
        Moves the stage to a specified position within the defined bounds.

        Parameters:
            position (float): The target position to move the stage to.
        """
        if not self.wrapper:
            print("Stage not initialized.")
            return

        try:
            current_position = self.wrapper.getPos()
            target_position = current_position + position
            # Ensure target position is within bounds
            target_position = max(min(target_position, self.bounds[1]), self.bounds[0])

            self.wrapper.moveAbs(self.axis, target_position)

            print(f"Move started, initial position: {current_position}")
            while self.is_moving():
                QThread.msleep(100)  # Short delay between checks
            print("Move complete.")
            pos = self.wrapper.getPos()
            print(f"Final position: {pos}")
            return pos
        except Exception as e:
            print(f"Error moving: {e}")

    def is_moving(self, threshold=0.0001):
        """
        Checks if the stage is currently moving by comparing its position at two different times.
        If the change in position exceeds a specified threshold, it is considered to be moving.

        Parameters:
            threshold (float): The minimum change in position to consider the stage as moving.

        Returns:
            bool: True if the stage is moving, False otherwise.
        """
        if not self.wrapper:
            print("Stage not initialized.")
            return False

        try:
            initial_pos = self.wrapper.getPos()
            QThread.msleep(10)  # Short delay to allow for movement detection
            final_pos = self.wrapper.getPos()

            # If the change in position is greater than the threshold, consider the stage as moving
            if abs(final_pos - initial_pos) > threshold:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error checking if stage is moving: {e}")
            return False