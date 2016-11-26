import sys
import time
import serial
import logging
from optparse import OptionParser
from ConfigParser import SafeConfigParser
from transitions import Machine

class alarmstate(object):
	""" class which manages the state of the alarm """
	""" need to import transitions by running 'pip install transitions' """
	""" got this from https://github.com/tyarkoni/transitions/blob/master/README.md """
	
	states = ["disarmed","armed","stay","triggered"]

	transitions = [
		{'trigger':'disarm','source':['armed','stay','triggered'],'dest':'disarmed'},
		{'trigger':'arm','source':'disarmed','dest':'armed','conditions':'checkAllSensorsAreNotActivated'},
		{'trigger':'stay','source':'disarmed','dest':'stay','conditions':'checkAllSensorsAreNotActivated'},
		{'trigger':'trigger','source':['armed','stay'],'dest':'triggered'}]
		
	def __init__(self,logger):
		self.machine = Machine(model=self,states=alarmstate.states,transitions=alarmstate.transitions,initial="stay")
		self.sensorstates = ''
		
		self.logger = logger					# used to log changes in alarm state
		self.sensorstate = ''					# used in checkAllSensorsAreNotActivated function
		
		self.machine.on_enter_disarmed('logStateChange')		# runs the logStateChange when setting alarm to disarmed
		self.machine.on_enter_armed('logStateChange')			# runs the logStateChange when setting alarm to armed
		self.machine.on_enter_stay('logStateChange')			# runs the logStateChange when setting alarm to stay
		self.machine.on_enter_triggered('logStateChange')		# runs the logStateChange when setting alarm to triggered
	
	def logStateChange(self):
		""" records all state changes in the log """
		self.logger.info('Alarm state: ' +  self.state)
		
	def checkAllSensorsAreNotActivated(self):
		""" checks all alarm sensors are not active """
		if "1" not in self.sensorstate:							# assumes all active sensors will be 1 and deactive sensors will be 0
			return True
		else:
			return False
	
class alarm(object):
	""" class which manages the alarm """
	
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	fh = logging.FileHandler('sensor_log')
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	
	alarmstate = alarmstate(logger)
	
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
		self.manageArgs(argv)

		self.logger.info('Starting up alarm system')
		self.logger.info('Alarm state: ' + self.alarmstate.state)

		print self.sensors.sections()
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
		if len(argv) > 1 and argv[1].endswith(".conf") :
			p = OptionParser()
			p.set_usage('run.py [options]')
			p.set_description(__doc__)
			p.add_option('-c', '--config', dest='config_file', action='store',
			help='Specify the configuration file. Default: alarm.conf') 
			opts, args = p.parse_args()
			self.manageConfig(opts.config_file)
		else:
			print 'ERROR: No sensor config file provided'

	def getSerialData(self):
		""" polls the serial interface and checks if any sensors changed state """
		out = ''
		while self.ser.inWaiting() > 0:
			out += self.ser.readline()
			out = out.rstrip('\n\r')
			self.alarmstate.sensorstate = out

		if (out != "") and (len(out) == len(self.sensors.sections())+2) and out.startswith('s') and out.endswith('e'):
			out = out[out.find('s')+1:out.find('e')]
			alarmstate.sensorstates = out
			
			for i, sensor in enumerate(self.sensors.sections()):
				if int(self.sensors.get(sensor, 'state')) != int(out[i]):
					self.sensors.set(sensor, 'state', str(out[i]))
					print self.sensors.get(sensor, 'name') + self.sensors.get(sensor, 'state')
					self.logger.info(self.sensors.get(sensor, 'name') + ' ' + self.sensors.get(sensor, 'state'))
					self.checkAlarmState(sensor)

	def checkAlarmState(self,sensor):
		""" checks the alarm state and decides whether or not to sound the siren """
		if self.alarmstate.state == 'disarmed':				
			#pass											# do nothing
			self.alarmstate.arm()							# added for testing purposes
		elif self.alarmstate.state == 'armed':				
			print "TODO:activate alarm siren"				# trigger alarm siren
			self.alarmstate.trigger()						# change alarm state to triggered
		elif self.alarmstate.state == 'stay':				
			if self.sensors.get(sensor, 'stay') == 'true':	# check config if sensor should be active during stay mode
				print "TODO:activate alarm siren"			# trigger alarm siren
				self.alarmstate.trigger()					# change alarm state to triggered
			else:
				pass
		else:												# assume alarm is in the triggered state
			pass


# run the code above
alarm(sys.argv)