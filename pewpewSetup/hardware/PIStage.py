from mmc_wrapper import MMC_Wrapper
from qtpy.QtCore import QThread

class PIStage:
    _controller_units = 'mm'  # Default units, update accordingly
    
    def __init__(self, bounds=[0, 25], stage='M1121DG', com_port='COM11', baud_rate=9600):
        self.bounds = bounds
        self.stage = stage
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.wrapper = None
        self.axis = None
        self.init_stage()

    def init_stage(self):
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
        try:
            devices = wrapper.MMC_initNetwork(3)  # Adjust the number as needed
            return devices
        except Exception as e:
            print(f"Error enumerating devices: {e}")
            return []

    def move_home(self):
        if not self.wrapper:
            print("Stage not initialized.")
            return

        try:
            self.wrapper.find_home()
            moving = True
            pos = self.wrapper.getPos()
            print(f"Initial position: {pos}, starting homing...")
            while moving:
                pos_tmp = self.wrapper.getPos()
                print(f"Current position: {pos_tmp}")
                moving = abs(pos - pos_tmp) > 0.0001
                QThread.msleep(100)
                pos = pos_tmp
            print("Homing complete.")
            self.wrapper.MMC_sendCommand('DH')  # Define as home
            QThread.msleep(500)
            pos = self.wrapper.getPos()
            print(f"Final position: {pos}")
        except Exception as e:
            print(f"Error moving home: {e}")

    def close(self):
        if self.wrapper:
            try:
                self.wrapper.MMC_COM_close()
                print("Connection closed successfully.")
            except Exception as e:
                print(f"Error closing connection: {e}")

    def stop_motion(self):
        if self.wrapper:
            try:
                self.wrapper.MMC_globalBreak()
                print("Motion stopped.")
            except Exception as e:
                print(f"Error stopping motion: {e}")

    def move(self, position):
        if not self.wrapper:
            print("Stage not initialized.")
            return

        try:
            current_position = self.wrapper.getPos()
            target_position = current_position + position
            target_position = max(min(target_position, self.bounds[1]), self.bounds[0])

            self.wrapper.moveAbs(self.axis, target_position)

            moving = True
            pos = self.wrapper.getPos()
            print(f"Starting move, initial position: {pos}")
            while moving:
                pos_tmp = self.wrapper.getPos()
                print(f"Current position: {pos_tmp}")
                moving = abs(pos - pos_tmp) > 0.0001
                QThread.msleep(100)
                pos = pos_tmp
            print("Move complete.")
            pos = self.wrapper.getPos()
            print(f"Final position: {pos}")
        except Exception as e:
            print(f"Error moving: {e}")

    def is_moving(self, threshold=0.0001):
        if not self.wrapper:
            print("Stage not initialized.")
            return False

        try:
            initial_pos = self.wrapper.getPos()
            QThread.msleep(10)  # Wait for a short period to check for movement
            final_pos = self.wrapper.getPos()

            # If the change in position is greater than the threshold, consider the stage as moving
            if abs(final_pos - initial_pos) > threshold:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error checking if stage is moving: {e}")
            return False

