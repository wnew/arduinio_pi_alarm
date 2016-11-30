import sys
import time
import serial
import logging
from optparse import OptionParser
from ConfigParser import SafeConfigParser
import RPi.GPIO as GPIO

SIREN_PIN  = 21
GARAGE_PIN = 16
GATE_PIN   = 20
FENCE_PIN  = 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SIREN_PIN,  GPIO.OUT)
GPIO.setup(GARAGE_PIN, GPIO.OUT)
GPIO.setup(GATE_PIN,   GPIO.OUT)
GPIO.setup(FENCE_PIN,  GPIO.OUT)
GPIO.output(SIREN_PIN,  True)
GPIO.output(GARAGE_PIN, True)
GPIO.output(GATE_PIN,   True)
GPIO.output(FENCE_PIN,  True)

class arduinoComms(object):
    """ class to manages the communication with the arduino """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('homeauto_log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # set the correct serial port for the OS
    if sys.platform.startswith('linux'):
        ser = serial.Serial(
        port = '/dev/ttyUSB0',
        baudrate = 115200,
        parity = serial.PARITY_NONE)
    # else assume windows
    else:
        ser = serial.Serial(
        port = 'COM6',
        baudrate = 115200,
        parity = serial.PARITY_NONE)


    def __init__(self, argv):
        """ init function : starts the loop to poll the serial interface """
        
        self.alarm = alarm(self.logger)
        self.userInput = userInput(self.logger)
        self.manageArgs(argv)
        self.logger.info('Starting up alarm system')
        self.ser.isOpen()
        while 1:
            data = self.getSerialData()

    def manageConfig(self, config_file):
        """ reads the configuration from the file and gets all the sensors """
        self.parser = SafeConfigParser()
        self.parser.read(config_file)
        self.sensors = self.parser

    def manageArgs(self, argv):
        """ reads the cmd line parameters and configures the script accordingly """
        """ checks whether a sensor config file has been provided """
        p = OptionParser()
        p.set_usage('run.py [options]')
        p.set_description(__doc__)
        p.add_option('-c', '--config', dest='config_file', action='store',
                     help='Specify the configuration file. default: alarm.conf',
                     default='alarm.conf') 
        opts, args = p.parse_args()
        self.manageConfig(opts.config_file)

    def getSerialData(self):
        """ polls the serial interface and checks if any sensors changed state """
        data = ''
        while self.ser.inWaiting() > 0:
            data += self.ser.readline()
            data = data.rstrip('\n\r')

        if (data != "") and (len(data) == len(self.sensors.sections())+2) and data.startswith('s') and data.endswith('e'):
            data = data[data.find('s')+1:data.find('e')]
            # send the sensors and the serial data to the alarm manager
            self.alarm.checkState(self.sensors, data)
            # send the sensors and the serial data to the home automation manager
            self.userInput.checkState(self.sensors, data, self.alarm)



class alarm(object):
    """ class which manages the alarm """

    # alarm states
    STARTUP   = 'STARTUP'
    DISARMED  = 'DISARMED'
    STAY      = 'STAY'
    ARMED     = 'ARMED'
    TRIGGERED = 'TRIGGERED'
    # initial alarm state
    alarmState = STARTUP
        
    def __init__(self, logger):
       self.logger = logger
       self.logger.info('Alarm starting up')
       self.logger.info('Alarm state: %s' %self.alarmState)
 
    def checkState(self, sensors, data):
        """ checks the alarm state and decides whether or not to sound the siren """
        # if the alarm is in startup state then loop throught the sensors and assign their states
        if self.alarmState == self.STARTUP:
            for i, sensor in enumerate(sensors.sections()):
                sensors.set(sensor, 'state', str(data[i]))  # initialise the states of the sensors
                sensors.set(sensor, 'triggered', '0')       # set sensor triggered values to 0
            self.alarmState = self.DISARMED
            self.logger.info('Sensor states initiallised')
            self.logger.info('Alarm state : %s' %'DISARMED')
        # if the alarm is not in startup state then check if any sensors have changed
        # and update the state accordingly
        else:
            for i, sensor in enumerate(sensors.sections()):
                if int(sensors.get(sensor, 'state')) != int(data[i]):
                    if sensors.get(sensor, 'user_input') == 'false':
                        sensors.set(sensor, 'state', str(data[i]))
                        sensors.set(sensor, 'triggered', '1')
                        print sensors.get(sensor, 'name') + sensors.get(sensor, 'state')
                        self.logger.info(sensors.get(sensor, 'name') + ' ' + sensors.get(sensor, 'state'))
                        if self.alarmState == self.ARMED:              
                            self.setAlarmState(self.TRIGGERED)                     # change alarm state to triggered
                        elif self.alarmState == self.STAY:               
                            if sensors.get(sensor, 'stay') == 'true':  # check config if sensor should be active during stay mode
                               self.setAlarmState(self.TRIGGERED)                         # change alarm state to triggered
            for i, sensor in enumerate(sensors.sections()):
                sensors.set(sensor, 'triggered', '0')

    def userInputCheckState(self, button, pressDuration):
        if button == 'set':
            if self.alarmState == self.DISARMED:
                if pressDuration > 1.5:
                    self.setAlarmState(self.STAY)
                else:
                    self.setAlarmState(self.ARMED)
            else:
                self.setAlarmState(self.DISARMED)
        elif button == 'panic':
            if pressDuration > 1.5:
                self.logger.info('Silent panic triggered')
                #TODO: long press could be used as a silent panic mode
            else:
                self.logger.info('Normal panic triggered')
                self.setAlarmState(self.TRIGGERED)

    def setAlarmState(self, state):
        self.alarmState = state
        self.logger.info('Alarm state : %s' %self.alarmState)
        if self.alarmState == self.DISARMED:
            GPIO.output(SIREN_PIN, True)
        elif self.alarmState == self.STAY:
            GPIO.output(SIREN_PIN, True)
        elif self.alarmState == self.ARMED:
            GPIO.output(SIREN_PIN, True)
        elif self.alarmState == self.TRIGGERED:
            GPIO.output(SIREN_PIN, False)


class userInput(object):
    """ class to manage the home automation side """

    def __init__(self, logger):
        self.alarmSetDepressTime = 0
        self.panicDepressTime = 0
        self.gateDepressTime = 0
        self.logger = logger
        self.logger.info('Home automation starting up')
    
    def checkState(self, sensors, data, alarm):
        for i, sensor in enumerate(sensors.sections()):
            if int(sensors.get(sensor, 'state')) != int(data[i]):
                if int(sensors.get(sensor, 'user_input') == 'true'):
                    sensors.set(sensor, 'state', str(data[i]))
                    print sensors.get(sensor, 'name')
                    # alarm set button 
                    if sensors.get(sensor, 'name') == 'alarm set':
                        # save the time that the alarm set button was depressed
                        if sensors.get(sensor, 'state') == '0':
                            self.logger.info('%s pressed' %(sensors.get(sensor, 'name')))
                            self.alarmSetDepressTime = time.time()
                        else:
                            self.logger.info('%s released' %(sensors.get(sensor, 'name')))
                            alarm.userInputCheckState('set', time.time()-self.alarmSetDepressTime)
                    # panic button
                    elif sensors.get(sensor, 'name') == 'panic':
                        # save the time that the panic button was depressed
                        if sensors.get(sensor, 'state') == '0':
                            self.logger.info('%s pressed' %(sensors.get(sensor, 'name')))
                            self.alarmSetDepressTime = time.time()
                        else:
                            self.logger.info('%s released' %(sensors.get(sensor, 'name')))
                            alarm.userInputCheckState('panic', time.time()-self.alarmSetDepressTime)
                    # gate button
                    elif sensors.get(sensor, 'name') == 'gate':
                        # save the time that the gate button was depressed
                        if sensors.get(sensor, 'state') == '0':
                            self.logger.info('%s pressed' %(sensors.get(sensor, 'name')))
                            self.gateDepressTime = time.time()
                        else:
                            self.logger.info('%s released' %(sensors.get(sensor, 'name')))
                            self.toggleGate(time.time()-self.gateDepressTime)
                    # garage button
                    elif sensors.get(sensor, 'name') == 'garage':
                        if sensors.get(sensor, 'state') == '1':
                            self.toggleGarage()
                    # fence button
                    elif sensors.get(sensor, 'name') == 'fence':
                        if sensors.get(sensor, 'state') == '1':
                            self.toggleFence()

    def toggleGate(self, duration):
        GPIO.output(GATE_PIN, False)
        time.sleep(0.5)
        GPIO.output(GATE_PIN, True)
        self.logger.info('Toggling gate state duration %s' % duration)
        if duration > 2:
            time.sleep(2)
            GPIO.output(GATE_PIN, False)
            time.sleep(0.5)
            GPIO.output(GATE_PIN, True)
            self.logger.info('Toggling gate state')


    def toggleGarage(self):
        GPIO.output(GARAGE_PIN, False)
        time.sleep(0.5)
        GPIO.output(GARAGE_PIN, True)
        self.logger.info('Toggling garage state')

    def toggleFence(self):
        GPIO.output(FENCE_PIN, False)
        time.sleep(0.5)
        GPIO.output(FENCE_PIN, True)
        self.logger.info('Toggling fence state')

# run the code above
arduinoComms(sys.argv)
