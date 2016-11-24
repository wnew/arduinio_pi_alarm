import sys
import time
import serial
import logging
from optparse import OptionParser
from ConfigParser import SafeConfigParser


class alarm(object):
  """ class which manages the alarm """

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)
  fh = logging.FileHandler('sensor_log')
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  logger.addHandler(fh)

  # alarm states
  DISARMED  = 0
  STAY      = 1
  ARMED     = 2
  TRIGGERED = 3
  alarm_state = DISARMED

  # set the correct serial port for the OS
  if sys.platform.startswith('linux'):
    ser = serial.Serial(
      port = '/dev/ttyUSB0',
      baudrate = 115200,
      parity = serial.PARITY_NONE)
  # else assume windows
  else:
    ser = serial.Serial(
      port = 'COM1',
      baudrate = 115200,
      parity = serial.PARITY_NONE)


  def __init__(self, argv):
    """ init function : starts the loop to poll the serial interface """
    self.manageArgs(argv)

    self.logger.info('Starting up alarm system')

    print self.sensors.sections()
    self.ser.isOpen()
    while 1:
      data = self.getSerialData()


  def manageConfig(self, config_file = 'alarm.conf'):
    """ reads the configuration from the file and gets all the sensors """
    self.parser = SafeConfigParser()
    self.parser.read(config_file)
    self.sensors = self.parser


  def manageArgs(self, argv):
    """ reads the cmd line parameters and configures the script accordingly """
    p = OptionParser()
    p.set_usage('run.py [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--config', dest='config_file', action='store',
        help='Specify the configuration file. Default: alarm.conf') 
    opts, args = p.parse_args(sys.argv[1:])
    self.manageConfig(opts.config_file)


  def getSerialData(self):
    """ polls the serial interface and checks if any sensors changed state """
    out = ''
    while self.ser.inWaiting() > 0:
      out += self.ser.readline()
      out = out.rstrip('\n\r')
      print out

      if (out != "") and (len(out) == len(self.sensors.sections())+2) and out.startswith('s') and out.endswith('e'):
        out = out[out.find('s')+1:out.find('e')]
        print out
        for i, sensor in enumerate(self.sensors.sections()):
          if int(self.sensors.get(sensor, 'state')) != int(out[i]):
            self.sensors.set(sensor, 'state', str(out[i]))
            print self.sensors.get(sensor, 'name') + self.sensors.get(sensor, 'state')
            self.logger.info(elf.sensors.get(sensor, 'name') + ' ' + self.sensors.get(sensor, 'state'))
            self.checkAlarmState()


  def checkAlarmState(self):
    """ checks the alarm state and decides whether or not to sound the siren """
    pass


# run the code above
alarm(sys.argv)
