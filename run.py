import sys
import time
import serial
import logging


class alarm(object):
  """ class which manages the alarm """

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)

  fh = logging.FileHandler('sensor_log')
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  logger.addHandler(fh)

  # a list of all the sensors in the system
  # the amount must match the length of the length of the string coming from the arduino
  sensors = [{'name': 'sliding door',       'pos':  0, 'pin':  2, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'front door',         'pos':  1, 'pin':  3, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'large garage door',  'pos':  2, 'pin':  4, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'back door',          'pos':  3, 'pin':  5, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'garage door',        'pos':  4, 'pin':  6, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'lounge side door',   'pos':  5, 'pin':  7, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'wooden gate',        'pos':  6, 'pin':  8, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'main gate',          'pos':  7, 'pin':  9, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'beam',               'pos': 12, 'pin': 14, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'beam tamper',        'pos': 13, 'pin': 15, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'kitchen pir',        'pos': 14, 'pin': 16, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'kitchen pir tamper', 'pos': 15, 'pin': 17, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'lounge pir',         'pos': 16, 'pin': 18, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'lounge pir tamper',  'pos': 17, 'pin': 19, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'garage pir',         'pos': 18, 'pin': 20, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'garage pir tamper',  'pos': 19, 'pin': 21, 'state': 1, 'triggered':False, 'stay':True},
             {'name': 'fence set',          'pos': 14, 'pin': 17, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'alarm set',          'pos': 15, 'pin': 18, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'panic button',       'pos': 16, 'pin': 19, 'state': 1, 'triggered':False, 'stay':False},
             {'name': 'mystery missing sensor',   'pos': 17, 'pin': 20, 'state': 1, 'triggered':False, 'stay':False}]

  # alarm states
  DISARMED  = 0
  STAY      = 1
  ARMED     = 2
  TRIGGERED = 3
  alarm_state = DISARMED

  # set the correct serial port for the OS
  if sys.plaform.startsWith('linux'):
    ser = serial.Serial(
      port='/dev/ttyACM0',
      baudrate=115200,
      parity=serial.PARITY_NONE
    )
  # assume windows
  else:
    ser = serial.Serial(
      port='COM1',
      baudrate=115200,
      parity=serial.PARITY_NONE
    )


  def __init__(self):
    """ init function : starts the loop to poll the serial interface """
    self.ser.isOpen()
    while 1:
        data = self.getSerialData()


  def getSerialData(self):
  """ the function that does the work polling the serial interface """
    out = ''
    while self.ser.inWaiting() > 0:
      out += self.ser.readline()
      out = out.rstrip('\n\r')
      if (out != "") and (len(out) == 22) and out.startswith('s') and out.endswith('e'):
        out = out[out.find('s')+1:out.find('e')]
        for sensor in self.sensors:
          if int(sensor['state']) != int(out[sensor['pos']]):
            sensor['state'] = int(out[sensor['pos']])
            print sensor['name'] + str(sensor['state'])
            self.logger.info(sensor['name'] + ' ' + str(sensor['state']))


# run the code above
alarm()
