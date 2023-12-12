from Keysight_N9917A import Keysight_N9917A

# Define the instrument's name, IP address, and other parameters
instrument_name = 'MyN9917A'
instrument_address = '192.168.1.120'
reset_to_defaults = True
measurement_class = 'VNA'
channel_number = 0

# Create an instance of the Keysight_N9917A class
n9917a_instance = Keysight_N9917A(
    name=instrument_name,
    address=instrument_address,
    reset=reset_to_defaults,
    meas_class=measurement_class,
    i_chan=channel_number
)

# Now you can use n9917a_instance to interact with the Keysight N9917A instrument
# For example:
# print("Instrument ID:", n9917a_instance.query_identification())