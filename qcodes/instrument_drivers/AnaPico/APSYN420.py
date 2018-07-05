import visa
import logging

from qcodes import VisaInstrument, validators as vals

log = logging.getLogger(__name__)

class APSYN420(VisaInstrument):
    '''
    qcodes driver for the AnaPico APSYN 420 Signal Generator.

    Args:
        name: instrument name
        address: VISA resource name of the instrument in format
                 'TCPIP0::192.168.15.100::inst0::INSTR'
        **kwargs: passed to base class

    TODO:
    - check initialisation settings and test functions
    '''
    def __init__(self, name: str, address: str, close_after_every_command: bool=True, **kwargs) -> None:

        super().__init__(name=name, address=address, **kwargs)
        self.visa_handle.write_termination = '\r\n'
        self.visa_handle.read_termination = None
        self.ask_raw('FREQ?')

        if close_after_every_command:
            self.visa_handle.close()
            self.visa_handle = None
            self.close_after()

        self.add_parameter('frequency', unit='Hz',
                            set_cmd='FREQ {:.3f}',
                            get_cmd='FREQ?',
                            vals=vals.Numbers(2490236,20e9),
                            get_parser=float)

        self.add_parameter('blanking',
                            set_cmd='OUTP:BLAN {}',
                            get_cmd='OUTP:BLAN?',
                            vals=vals.OnOff(),
                            get_parser=self.parse_on_off)

        self.add_parameter('output',
                            set_cmd='OUTP {}',
                            get_cmd='OUTP?',
                            vals=vals.OnOff(),
                            get_parser=self.parse_on_off)

        self.add_parameter('pulm_state',
                            set_cmd='PULM:STAT {}',
                            get_cmd='PULM:STAT?',
                            vals=vals.OnOff(),
                            get_parser=self.parse_on_off)

        self.add_parameter('pulm_polarity',
                            set_cmd='PULM:POL {}',
                            get_cmd='PULM:POL?',
                            val_mapping={'Normal':'NORM', 'Inverted':'INV'},
                            get_parser=self.parse_str,
                            docstring='Pulse Modulation Input Polarity \
                                       Mode: "Normal" or "Inverted"')

        self.add_parameter('pulm_source',
                            set_cmd='PULM:POL {}',
                            get_cmd='PULM:POL?',
                            val_mapping={'Internal':'INT', 'External':'EXT'},
                            get_parser=self.parse_str)

    def write_raw_close(self, cmd):
        """
        Low-level interface to ``visa_handle.write``.

        Args:
            cmd (str): The command to send to the instrument.
        """
        log.debug("Writing to instrument {}: {}".format(self.name, cmd))

        if not self.visa_handle:
            self.visa_handle = visa.ResourceManager().open_resource(self._address)

        nr_bytes_written, ret_code = self.visa_handle.write(cmd)
        self.check_error(ret_code)
        
        self.visa_handle.close()
        self.visa_handle = None

    def ask_raw_close(self, cmd):
        """
        Low-level interface to ``visa_handle.ask``.

        Args:
            cmd (str): The command to send to the instrument.

        Returns:
            str: The instrument's response.
        """
        log.debug("Querying instrument {}: {}".format(self.name, cmd))

        if not self.visa_handle:
            self.visa_handle = visa.ResourceManager().open_resource(self._address)

        return self.visa_handle.query(cmd)

        self.visa_handle.close()
        self.visa_handle = None

    def close_after(self):
        self.ask_raw = self.ask_raw_close
        self.write_raw = self.write_raw_close

    def dont_close_after(self):
        self.ask_raw = VisaInstrument.ask_raw
        self.write = VisaInstrument.write_raw

    def parse_on_off(self, stat):
        if stat.startswith('0'):
            stat = 'off'
        elif stat.startswith('1'):
            stat = 'on'
        return stat

    def parse_str(self, string):
        return string.strip().upper()

    def set_external_reference(self, frequency = 10e6):
        '''
        Sets external reference and outputs the 10 MHz.
        '''
        logging.debug('Setting the Oscillator source to external')
        self.write('ROSC:SOUR EXT')
        self.write('ROSC:EXT:FREQ %d' % frequency)
        self.write('ROSC:OUTP:STATE 1')
        self.write('ROSC:OUTP:FREQ %d' % frequency)

        while int(self.ask('ROSC:LOCK?').strip()) != 1:
            print('Waiting for lock on APSYN')
            qt.msleep(1)

#       self.add_parameter('blanking', type=types.BooleanType,
#                           flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET)
#       self.add_parameter('rf', type=types.BooleanType,
#                           flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET)
#       self.add_parameter('frequency', type=types.FloatType, format='%.6e',
#                          flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET,
#                          units=self._freq_unit_symbol, minval=0.65e9/self._freq_unit, maxval=20.4e9/self._freq_unit)
#       self.add_parameter('pulm_state', type=types.BooleanType,
#                           flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET)
#       self.add_parameter('pulm_polarity', type=types.StringType,
#                           flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET,
#                           format_map = {
#                             "NORM" : "Normal",
#                             "INV" : "Inverted"
#                           })
#       self.add_parameter('pulm_source', type=types.StringType,
#                           flags=Instrument.FLAG_GETSET|Instrument.FLAG_GET_AFTER_SET,
#                           format_map = {
#                             "INT" : "Internal",
#                             "EXT" : "External"
#                           })

#       if reset:
#           self.reset()

#   # def __del__(self):
#   #   self._visainstrument.close()

# # --------------------------------------
# #           functions
# # --------------------------------------
#   def remove(self):
#       self._visainstrument.close()
#       super(AnaPico_APSYN420, self).remove()
        
#   def reset(self):
#       '''
#       Resets the APSYN420 to default settings.
#       '''
#       logging.debug('Resetting ...')
#       self._visainstrument.write('*RST')

#   def get_instrument(self):
#       '''
#       Returns the instrument object directly to make queries.
#       Note: This function should only be used for testing purposes
#       since it does not go through qtlab.
#       '''
#       return self._visainstrument

#   def do_get_blanking(self):
#       '''
#       Returns the blanking state.
#       '''
#       return int(self._visainstrument.query('OUTP:BLAN?').strip) == 1

#   def do_set_blanking(self, state):
#       '''
#       Sets the blanking state.
#       '''
#       logging.debug('Setting blanking %r' % state)
#       self._visainstrument.write('OUTP:BLAN %d' % state)

#   def do_get_output(self):
#       '''
#       Returns the output state.
#       '''
#       logging.debug('Reading the output state.')
#       return int(self._visainstrument.query('OUTP?').strip()) == 1
    
#   def do_set_output(self, state):
#       '''
#       Sets the output state.
#       '''
#       logging.debug('Setting the output state to %r' % state)
#       self._visainstrument.write('OUTP %d' % state)

#   def rf_on(self):
#       '''
#       Turns on RF output.
#       '''
#       self.set_output(True)

#   def rf_off(self):
#       '''
#       Turns off RF output.
#       '''
#       self.set_output(False)

#   def do_get_frequency(self):
#       '''
#       Returns the frequency.
#       '''
#       logging.debug('Reading the frequency.')
#       return float(self._visainstrument.query('FREQ?').strip())

#   def do_set_frequency(self, freq):
#       '''
#       Sets the frequency.
#       '''
#       logging.debug('Setting the frequency to %e.' % freq)
#       self._visainstrument.write('FREQ %e' % freq)

#   def do_get_pulm_state(self):
#       '''
#       Returns the Pulse Modulation State.
#       '''
#       logging.debug('Reading the pulse modulation state.')
#       return int(self._visainstrument.query('PULM:STAT?').strip()) == 1

#   def do_set_pulm_state(self, state):
#       '''
#       Sets the Pulse Modulation State.
#       '''
#       logging.debug('Setting the pulse modulation state to %r.' % state)
#       self._visainstrument.write('PULM:STAT %d' % state)

#   def do_get_pulm_polarity(self):
#       '''
#       Returns pulse modulation polarity.
#       '''
#       logging.debug('Reading Pulse Modulation Polaity Status')
#       return self._visainstrument.query('PULM:POL?')

#   def do_set_pulm_polarity(self, polarity):
#       '''
#       Sets the desired polarity for pulse modulation.
#       '''
#       polarity = polarity.strip().upper()
#       logging.debug('Setting the Pulse Modulation Polarity to %s' % polarity)
#       self._visainstrument.write('PULM:POL %s' % polarity)

#   def do_get_pulm_source(self):
#       '''
#       Returns pulse modulation source.
#       '''
#       logging.debug('Reading Pulse Modulation Source Status')
#       return self._visainstrument.query('PULM:SOUR?')

#   def do_set_pulm_source(self, source):
#       '''
#       Sets the desired source for pulse modulation.
#       '''
#       source = source.strip().upper()
#       logging.debug('Setting the Pulse Modulation Source to %s' % source)
#       self._visainstrument.write('PULM:SOUR %s' % source)

#   def do_get_pulm_int_period(self):
#       '''
#       Returns internal pulse modulation period.
#       '''
#       logging.debug('Reading the Internal Pulse Modulation Period.')
#       return float(self._visainstrument.query('PULM:INT:PER').strip())

#   def do_set_pulm_int_period(self, period):
#       '''
#       Sets internal pulse modulation period.
#       '''
#       logging.debug('Setting the Internal Pulse Modulation Period to %e' % period)
#       self._visainstrument.write('PULM:INT:PER %e' % period)

#   def do_get_pulm_int_pulse_width(self):
#       '''
#       Returns internal pulse modulation pulse width.
#       '''
#       logging.debug('Reading the Internal Pulse Modulation Pulse Width.')
#       return float(self._visainstrument.query('PULM:INT:PWID').strip())

#   def do_set_pulm_int_pulse_width(self, width):
#       '''
#       Sets internal pulse modulation pulse width.
#       '''
#       logging.debug('Setting the Internal Pulse Modulation Pulse Width to %e' % width)
#       self._visainstrument.write('PULM:INT:PWID %e' % width)

#   def set_external_reference(self, frequency = 10e6):
#       '''
#       Sets external reference and outputs the 10 MHz.
#       '''
#       logging.debug('Setting the Oscillator source to external')
#       self._visainstrument.write('ROSC:SOUR EXT')
#       self._visainstrument.write('ROSC:EXT:FREQ %d' % frequency)
#       self._visainstrument.write('ROSC:OUTP:STATE 1')
#       self._visainstrument.write('ROSC:OUTP:FREQ %d' % frequency)

#       try:
#           while int(self._visainstrument.query('ROSC:LOCK?').strip()) != 1:
#               print 'Waiting for lock on APSYN'
#               qt.msleep(0.1)
#       except KeyboardInterrupt:
#           print 'Interrupted before lock was achieved on APSYN 420'