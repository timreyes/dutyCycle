# import math
# import numpy

from saleae.range_measurements import DigitalMeasurer

DUTY_CYCLE = 'dutyCycle'

class DutyCycleMeasurer(DigitalMeasurer):
    supported_measurements = [DUTY_CYCLE]

    # Initialize your measurement extension here
    # Each measurement object will only be used once, so feel free to do all per-measurement initialization here
    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)

        self.first_transition_type = None
        self.first_transition_time = None
        self.last_transition_time = None
        self.total_pulse_length_of_first_type = None
        self.total_pulse_length_of_second_type = None
        self.first_pulse_length = None


    # This method will be called one or more times per measurement with batches of data
    # data has the following interface
    #   * Iterate over to get transitions in the form of pairs of `Time`, Bitstate (`True` for high, `False` for low)
    # `Time` currently only allows taking a difference with another `Time`, to produce a `float` number of seconds
    def process_data(self, data):
        for t, bitstate in data:
            # Find the first transition type and time
            if self.first_transition_type is None:
                self.first_transition_type = bitstate
                self.first_transition_time = t
                self.last_transition_time = t

            # If the current bitstate is the opposite of the first transition type, then the most recent pulse is of the first pulse type in a complete period.
            elif bitstate == (not self.first_transition_type):
                # Measure the length of the last pulse and save the current transition time for the next cycle
                self.first_pulse_length = t - self.last_transition_time
                self.last_transition_time = t
                

            # Check if the most recent pulse is of the second pulse type in a complete period.
            # If the current bitstate is equal to the first transition type, then we have reached a full period. The current t minus the last_transition_t will give
            # us the length of the most recent pulse that is NOT the first transition type. (e.g. if first transition type is positive, then the most recent pulse 
            # is a neg. pulse)
            elif bitstate == self.first_transition_type:
                # Measure the length of the last pulse and save the current transition time for the next cycle
                current_pulse_length = t - self.last_transition_time
                self.last_transition_time = t
                self.total_pulse_length_of_second_type += current_pulse_length

                # Wait until entire period is complete before tallying up the first pulse length
                self.total_pulse_length_of_first_type += self.first_pulse_length

    # This method is called after all the relevant data has been passed to `process_data`
    # It returns a dictionary of the request_measurements values
    def measure(self):
        values = {}

        if DUTY_CYCLE in self.requested_measurements:
            # We need at least one whole period within the measurement selection to calculate duty cycle
            if self.total_pulse_length_of_second_type is not None:
                # If first transition type was a rising edge (i.e. boolean TRUE), then the duty cycle will be the
                # total first pulse type length divided by the total length of all complete periods combined
                if self.first_transition_type:
                    values[DUTY_CYCLE] = 100 * (float(self.total_pulse_length_of_first_type) / float(self.total_pulse_length_of_first_type + self.total_pulse_length_of_second_type))
                # Else If first transition type was a falling edge (i.e. boolean FALSE), then the duty cycle will be the
                # total second pulse type length divided by the total length of all complete periods combined
                else:
                    values[DUTY_CYCLE] = 100 * (float(self.total_pulse_length_of_second_type) / float(self.total_pulse_length_of_first_type + self.total_pulse_length_of_second_type))

        return values
