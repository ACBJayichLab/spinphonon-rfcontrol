import types
import logging
import numpy as np
from time import sleep
from visainstrument import SCPI_Instrument
from instrument import Instrument

class Keysight_N9917A(SCPI_Instrument):
    '''
    This is the driver for the Keysight N9917A FieldFox Handheld Network Analyzer.

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keysight_N9917A', address='<IP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False, meas_class='VNA', i_chan=1, **kwargs):
        '''
        Initializes the Keysight N9917A and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : IP address
          reset (bool)     : resets to default values, default=False
          meas_class (str) : Measurement class (e.g., 'CAT', 'VNA', 'SA')  (Cable and antenna tester (CAT) + Vector network analyzer (VNA) + Spectrum analyzer (SA) )
          i_chan (int)     : Channel number on FieldFox for this instance of measurement class
        '''
        super(Keysight_N9917A, self).__init__(name, address, **kwargs)
        if reset:
            self.reset_to_defaults()

        self.add_parameter('chan', type=int, flags=Instrument.FLAG_GET)
        self.meas_class = meas_class
        self._chan = i_chan
        ch = str(i_chan)
        assert meas_class in ['CAT', 'VNA', 'SA'], 'Keysight_N9917A does not support meas_class = ' + meas_class
        self.add_parameter('meas_class', type=str, flags=Instrument.FLAG_GET)
        self._meas_class = meas_class


        self.add_scpi_parameter("start_freq", "S    ENS"+ch+":FREQ:STAR", "%d", units="Hz", type=float, gui_group='sweep') #good
        self.add_scpi_parameter('stop_freq', "SENS"+ch+":FREQ:STOP", "%d", units="Hz", type=float, gui_group='sweep') #good
        self.add_scpi_parameter("start_pow", "SOUR"+ch+":POW:STAR", "%d", units="dBm", type=float, gui_group='sweep') #good
        self.add_scpi_parameter('stop_pow', "SOUR"+ch+":POW:STOP", "%d", units="dBm", type=float, gui_group='sweep')  #good
        self.add_scpi_parameter('center_pow', "SOUR"+ch+":POW:CENT", "%d", units="dBm", type=float, gui_group='sweep') #good
        self.add_scpi_parameter('cw_freq',"SENS"+ch+":FREQ:CW", "%d", units='Hz', type=float) # now good
        self.add_scpi_parameter('center_freq', "SENS"+ch+":FREQ:CENT", "%d", units="Hz", type=float, gui_group='sweep') #good
        self.add_scpi_parameter('span', "SENS"+ch+":FREQ:SPAN", "%d", units="Hz", type=float, gui_group='sweep') #good 
        self.add_scpi_parameter('if_bandwidth', "SENS"+ch+":BAND", "%d", units="Hz", type=float, gui_group='averaging') #good
        self.add_scpi_parameter('power', "SOUR"+ch+":POW", "%.2f", units="dBm", type=float) #good
        self.add_scpi_parameter('power_on', 'OUTP', '%i', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_scpi_parameter('points', "SENS"+ch+":SWE:POIN", "%d", type=int, gui_group='sweep') #good
        self.add_scpi_parameter('average_factor', "SENS"+ch+":AVER:COUN", "%d", type=int, gui_group='averaging') #good
        self.add_scpi_parameter('averaging_state', 'SENS'+ch+':AVER', '%i', type=bool, flags=Instrument.FLAG_GETSET, gui_group='averaging')
        self.add_scpi_parameter('averaging_mode', 'SENS'+ch+':AVER:MODE', '%s', type=str, gui_group='averaging',
                                flags=Instrument.FLAG_GETSET, format_map={'POIN': 'point', 'SWE': 'sweep'})
        
        # selecting measurements
        self.add_scpi_parameter('meas_select', "CALC"+ch+":PAR:SEL", '%s', type=str, flags=Instrument.FLAG_GETSET) #new
        self.add_scpi_parameter('meas_select_trace', 'CALC'+ch+':PAR:MNUM', '%d', type=int, flags=Instrument.FLAG_GETSET)
        self.add_scpi_parameter('meas_class_curr', "SENS"+ch+":CLAS:NAME", '%s', type=str, flags=Instrument.FLAG_GET) #new
        
        #system
        self.add_scpi_parameter('error', "SYST:ERR", "%s", type=str, flags=Instrument.FLAG_GET) #good
        self.add_scpi_parameter('active_chan', "SYST:ACT:CHAN", '%s', type=str, flags=Instrument.FLAG_GET)
        self.add_scpi_parameter('active_measurement', "SYST:ACT:MEAS", '%s', type=str, flags=Instrument.FLAG_GET) #new

#        for lab in [['mixer',1],['VNA',2],['SPEC',3]]:            
#             self.add_scpi_parameter(lab[0]+'_INP_freq_fixed', 'SENS'+lab[1]':MIX:INP:FREQ:FIX', '%d', units='Hz', type = float, gui_group=lab[0])
            
        self.add_scpi_parameter('sweep_time', 'SENS'+ch+':SWE:TIME', '%.8f', units="s", type=float,
                                flags=Instrument.FLAG_GET, gui_group='sweep') # now good, yay
        self.add_scpi_parameter('segment_sweep_time', 'SENS'+ch+':SEGM:SWE:TIME', '%.8f', units="s", type=float,
                                flags=Instrument.FLAG_GET, gui_group='sweep') #now good
        
        if meas_class == 'SA':
            # spectrum analyzer specific parameters
            self.add_scpi_parameter('spec_rbw_shape', 'SENS'+ch+':SA:BAND:SHAP', '%s', type=str,
                                    flags=Instrument.FLAG_GETSET, gui_group='spec',
                                    format_map={'GAUS':'Gaussian', 'FLAT':'flat top', 'KAIS':'Kaiser',
                                                'BLAC':'Blackman', 'NONE':'none'})
            self.add_scpi_parameter('spec_detector_func', 'SENS'+ch+':SA:DET:FUNC', '%s', type=str,
                                    flags=Instrument.FLAG_GETSET, gui_group='spec',
                                    format_map={'PEAK':'peak', 'AVER':'average', 'SAMP':'sample',
                                                'NORM':'normal', 'PSAM':'peak sample', 'PAV':'peak average'})
            self.add_scpi_parameter('spec_vbw_aver_type', 'SENS'+ch+':SA:BAND:VID:AVER:TYPE', '%s', type=str,
                                    flags=Instrument.FLAG_GETSET, gui_group='spec',
                                    format_map={'VOLT':'voltage', 'POW':'power', 'LOG':'log',
                                                'VMAX':'voltage max', 'VMIN':'voltage min'})
            self.add_scpi_parameter('spec_rbw', 'SENS'+ch+':SA:BAND', '%d', units='Hz',
                                    type=float, gui_group='spec')
            self.add_scpi_parameter('spec_vbw', 'SENS'+ch+':SA:BAND:VID', '%d', units='Hz',
                                    type=float, gui_group='spec')

    def reset_to_defaults(self):
        '''
        Resets the instrument to default values.
        '''
        # Implement the reset logic specific to Keysight_N9917A
        pass
