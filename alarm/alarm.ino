// this project uses the arduino to poll the alarm sensors and to send a serial
// message to the rpi if there is any change in the state of the sensors. This
// means that the rpi is required to handle the alarm state.

// list of sensor pins, set this to the number of sensors in your system.
// this must match the number of sensors in your rpi python code

#if defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
const uint8_t pins[] = {2,   3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
                        18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
                        34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
                        50, 51, 52, 53, 54, 55, 56};
int pin_states[]     = {1, 1, 1, 1, 1, 1, 1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                        1, 1, 1, 1, 1, 1, 1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                        1, 1, 1, 1, 1, 1, 1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                        1, 1, 1, 1, 1, 1, 1};
#else
const uint8_t pins[] = {2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19};
int pin_states[]     = {1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1};
#endif

bool state_changed = false;

// setup method
void setup() {
  Serial.begin(115200);
  Serial.println("Arduino Alarm System 4.0");
  
  // setup pins as outputs with pullup resistors
  for (int i  = 0; i < sizeof(pins); i++) {
    pinMode(pins[i], INPUT_PULLUP);
  }
  // read and set the initial state of the pins
  for (int i  = 0; i < sizeof(pins); i++) {
    pin_states[i] = digitalRead(pins[i]);
  }
}


// main loop
void loop() {
  delay(25);

  // read the pins and compare to the current state, if different save the changed state
  for (int i = 0; i < sizeof(pins); i++) {
  	if (digitalRead(pins[i]) != pin_states[i]) {
      state_changed = true;
      pin_states[i] = !pin_states[i];
    }
  }

  // if the state of any pin has changed, send the states over serial to the pi
  if (state_changed == true) {
    state_changed = false;
    String serial_str = "s";
    for (int i = 0; i < sizeof(pins); i++) {
      serial_str = serial_str + pin_states[i];
    }
    serial_str = serial_str + "e";
    Serial.println(serial_str);
  }
  one_second();
}


unsigned long previousMillis = 0; // last time update
long interval = 1000; // interval at which to do something (milliseconds)

// send the state of the sensors every second
// this adds to the robustness of the sensors
// also serves to send the states to the rpi before anything changes
void one_second() {
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis > interval) {
    previousMillis = currentMillis;  

    String serial_str = "s";
    for (int i = 0; i < sizeof(pins); i++) {
      serial_str = serial_str + pin_states[i];
    }
    serial_str = serial_str + "e";
    Serial.println(serial_str);
  }
}
