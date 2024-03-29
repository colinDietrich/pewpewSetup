import pyvisa

def find(searchString):
    """
    Searches for devices matching the specified search string and prints the results.

    :param searchString: The search pattern to use for finding devices.
    """
    # Create a resource manager object
    resourceManager = pyvisa.ResourceManager()

    print(f"Find with search string '{searchString}':")
    # List resources that match the search string
    devices = resourceManager.list_resources(searchString)
    if len(devices) > 0:
        for device in devices:
            print(f"\t{device}")
    else:
        print("... didn't find anything!")

    # Close the resource manager to clean up resources
    resourceManager.close()

# Find all devices and interfaces
print('Find all devices and interfaces:\n')
find('?*')

# Different search strings can be used to specify other device types. Common examples include:

# All instruments (excluding interfaces, backplanes, or memory access)
find('?*INSTR')
# PXI modules
find('PXI?*INSTR')
# USB devices
find('USB?*INSTR')
# GPIB instruments
find('GPIB?*INSTR')
# GPIB interfaces
find('GPIB?*INTFC')
# GPIB instruments on the GPIB0 interface
find('GPIB0?*INSTR')
# LAN instruments
find('TCPIP?*INSTR')
# SOCKET (::SOCKET) instruments
find('TCPIP?*SOCKET')
# VXI-11 (inst) instruments
find('TCPIP?*inst?*INSTR')
# HiSLIP (hislip) instruments
find('TCPIP?*hislip?*INSTR')
# RS-232 instruments
find('ASRL?*INSTR')

print('Done.')