#define NUM_COLUMNS (4)
#define NUM_ROWS (4)
#define NUM_SELECT_PINS (4)
#define NUM_COLOURS (3)

#define SOP ('~')

#define OP_NAME_REQUEST (0x00)
#define OP_NAME_REPLY (0x01)
#define OP_STATE_REQUEST (0x02)
#define OP_STATE_REPLY (0x03)

#define MAX_INCOMING_PACKET_LEN (128)

#define LED_BUILTIN (13)

/********* PACKET HANDLING VARIABLES **********/
uint8_t incoming_buffer[MAX_INCOMING_PACKET_LEN];
int buffer_write_index = 0;
int header_len = 4;

const char board_id[] = "USB_CONTROLLER_000";
const uint16_t board_id_len = 18;


/********* CONTROL PAD VARIABLES **********/
const uint8_t signal_pin = 9;
const uint8_t enable_pin = 2;
const uint8_t select_pins[NUM_SELECT_PINS] = {3, 4, 5, 6};

static const uint8_t led_column_pins[NUM_COLUMNS]   = {17, 18, 19, 12};
uint8_t led_output_id[NUM_ROWS][NUM_COLOURS] = { {14, 12, 13}, {10, 8, 9}, {6, 4, 5}, {2, 0, 1} };

static const uint8_t switch_column_pins[NUM_COLUMNS]   = {13, 14, 15, 16};
static const uint8_t switch_row_ids[NUM_COLUMNS]   = {15, 11, 7, 3};

uint16_t button_pressed_since_update = 0x0000;


/********* SLIDER VARIABLES **********/
const int num_sliders = 4;
const int slider_pins[] = {20, 21, 22, 23};
uint16_t slider_vals[] = {0, 0, 0, 0};
float slider_smoothing_factor = 0.7;

uint8_t led_colours[NUM_COLUMNS][NUM_ROWS][NUM_COLOURS] = { { {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0} },
                                                            { {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0} },
                                                            { {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0} },
                                                            { {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0} } };

bool switch_state[NUM_COLUMNS][NUM_ROWS] =  { { false, false, false, false },
                                              { false, false, false, false },
                                              { false, false, false, false },
                                              { false, false, false, false } };

int last_switch_change[NUM_COLUMNS][NUM_ROWS] = { { 0, 0, 0, 0 },
                                                  { 0, 0, 0, 0 },
                                                  { 0, 0, 0, 0 },
                                                  { 0, 0, 0, 0 } };

const int debounce_interval = 100;
int currentLedState = 0;


void setup() {
  Serial.begin(9600);
  for(int i = 0; i < NUM_COLUMNS; i++)
  {
    pinMode(led_column_pins[i], OUTPUT);
    digitalWrite(led_column_pins[i], HIGH);
    
    pinMode(switch_column_pins[i], OUTPUT);
    digitalWrite(switch_column_pins[i], HIGH);
  }
  
  for(int i = 0; i < NUM_SELECT_PINS; i++)
  {
    pinMode(select_pins[i], OUTPUT);
    digitalWrite(select_pins[i], LOW);
  }
  
  //digitalWrite(signal_pin, HIGH);
  pinMode(signal_pin, INPUT_PULLUP);
  pinMode(enable_pin, OUTPUT);
  digitalWrite(enable_pin, HIGH);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

float f[3] = {11.53, 17.93, 13.27};
float offset_per_pixel = (NUM_ROWS*NUM_COLUMNS) / 255;

void loop() {
  // put your main code here, to run repeatedly:
  //write_leds();
  read_switches();
  read_sliders();
  handle_incoming();
}

void handle_incoming() {
  while (Serial.available()) {
    uint8_t new_byte = Serial.read();
    //Serial.write(new_byte);

    // if we are between packets, sync on SOP
    if (buffer_write_index != 0 || new_byte == SOP) {
      incoming_buffer[buffer_write_index++] = new_byte;
      if (buffer_write_index == header_len) {
        digitalWrite(LED_BUILTIN, HIGH);
        parse_header();
        buffer_write_index = 0;
      }
    }
  }
}

void parse_header() {
  uint8_t sop = incoming_buffer[0];
  uint8_t op = incoming_buffer[1];
  uint8_t payload_len = (incoming_buffer[2]<<8) | incoming_buffer[3];

  if (sop != SOP) {
    return;
  }
  
  if (op == OP_NAME_REQUEST) {
    send_name_reply();
  }

  else if (op == OP_STATE_REQUEST) {
    send_state_reply();
  }
}

void send_name_reply() {
  Serial.write("~");
  Serial.write(OP_NAME_REPLY);
  Serial.write(board_id_len >> 8);
  Serial.write(board_id_len & 0xff);
  Serial.write(board_id);
  
  digitalWrite(LED_BUILTIN, LOW);
}

void send_state_reply() {
  Serial.write("~");
  Serial.write(OP_STATE_REPLY);

  uint16_t len = 0;
  len += 1; // button bitfield width field
  len += sizeof(button_pressed_since_update); // button bitfield
  len += 1; // num sliders field
  len += num_sliders*2; // sliders, all 2 bytes
  Serial.write(len >> 8);
  Serial.write(len & 0xff);

  Serial.write(sizeof(button_pressed_since_update)); // button bitfield len
  Serial.write((uint8_t)(button_pressed_since_update >> 8)); // button bitfield
  Serial.write((uint8_t)(button_pressed_since_update & 0xff)); // button bitfield
  Serial.write(num_sliders); // num slider fields

  for (int i = 0; i < num_sliders; i++) {
    Serial.write(slider_vals[i] >> 8);
    Serial.write(slider_vals[i] & 0xff);
  }

  button_pressed_since_update = 0x0000;
}


void read_switches() {
  pinMode(signal_pin, INPUT_PULLUP);
  
  for (int col = 0; col < NUM_COLUMNS; col++) {
    digitalWrite(switch_column_pins[col], LOW);
    
    for (int row = 0; row < NUM_ROWS; row++) {
      digitalWrite(enable_pin, LOW);
      uint8_t index = switch_row_ids[row];

      for (int i = 0; i < NUM_SELECT_PINS; i++) {
        digitalWrite(select_pins[i], (index >> i) & 1);
      }

      delay(1); // remove this at risk of madness

      bool new_switch_state = !digitalRead(signal_pin);

      if (new_switch_state != switch_state[col][row]) {
        if (last_switch_change[col][row] + debounce_interval < millis()) {
          last_switch_change[col][row] = millis();
          switch_state[col][row] = new_switch_state;
          //Serial.print("Switch "); Serial.print(col*NUM_ROWS + row); Serial.print(" now "); Serial.println(new_switch_state);
          button_pressed_since_update |= 1u<<(sizeof(button_pressed_since_update)*8-1 - (col*NUM_ROWS + row));
          //Serial.println(button_pressed_since_update, HEX);
        }
      }

      digitalWrite(enable_pin, HIGH);
    }
    
    digitalWrite(switch_column_pins[col], HIGH);
  }
}

void read_sliders() {
  for (int i = 0; i < num_sliders; i++) {
    slider_vals[i] *= slider_smoothing_factor;
    slider_vals[i] += analogRead(slider_pins[i]) * (1.0 - slider_smoothing_factor);
  }
}


void write_leds() {
  pinMode(signal_pin, OUTPUT);
  
  for (int col = 0; col < NUM_COLUMNS; col++) {
    digitalWrite(led_column_pins[col], LOW);
    
    for (int row = 0; row < NUM_ROWS; row++) {
      for (int channel = 0; channel < NUM_COLOURS; channel++) {
        digitalWrite(enable_pin, LOW);
        
        uint8_t index = led_output_id[row][channel];

        for (int i = 0; i < NUM_SELECT_PINS; i++) {
          digitalWrite(select_pins[i], (index >> i) & 1);
        }

        analogWrite(signal_pin, led_colours[col][row][channel]);
        
        delay(1);
        analogWrite(signal_pin, 0);
        digitalWrite(enable_pin, HIGH);

      }
    }
    
    digitalWrite(led_column_pins[col], HIGH);
  }
}



/*
                                             
#define RED_CHANNEL 0
#define BLUE_CHANNEL 0
#define GREEN_CHANNEL 0
// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint8_t Wheel(byte WheelPos, int channel) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    if (channel == RED_CHANNEL) {
      return 255 - WheelPos*3;
    }
    else if (channel == GREEN_CHANNEL) {
      return 0;
    }
    else {
      return WheelPos * 3;
    }
  }
  else if(WheelPos < 170) {
    WheelPos -= 85;
    
    if (channel == RED_CHANNEL) {
      return 0;
    }
    else if (channel == GREEN_CHANNEL) {
      return WheelPos * 3;
    }
    else {
      return 255 - WheelPos;
    }
  }
  
  else {
    WheelPos -= 170;
    
    if (channel == RED_CHANNEL) {
      return WheelPos * 3;
    }
    else if (channel == GREEN_CHANNEL) {
      return 255 - WheelPos * 3;
    }
    else {
      return 0;
    }
  }
}*/
