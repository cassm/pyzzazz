/*Required Connections
  --------------------
    pin 2:  LED Strip #1    OctoWS2811 drives 8 LED Strips.
    pin 14: LED strip #2    All 8 are the same length.
    pin 7:  LED strip #3
    pin 8:  LED strip #4    A 100 ohm resistor should used
    pin 6:  LED strip #5    between each Teensy pin and the
    pin 20: LED strip #6    wire to the LED strip, to minimize
    pin 21: LED strip #7    high frequency ringining & noise.
    pin 5:  LED strip #8
    pin 15 & 16 - Connect together, but do not use
    pin 4 - Do not use
    pin 3 - Do not use as PWM.  Normal use is ok.
*/

#include <OctoWS2811.h>

const int onboard_led = 13;
const uint8_t frame_start_char = '~';
const uint8_t frame_end_char = '|';

uint64_t last_show = 0;
uint64_t show_interval = 1000/24;

uint64_t iter = 0;
bool currentState = 0;

const uint8_t PROGMEM gamma_table[255] = {   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
                                      0,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   2,   2,   2,
                                      2,   2,   2,   3,   3,   3,   3,   3,   4,   4,   4,   4,   5,   5,   5,   5,
                                      6,   6,   6,   6,   7,   7,   7,   8,   8,   8,   9,   9,   9,  10,  10,  10,
                                     11,  11,  11,  12,  12,  13,  13,  14,  14,  14,  15,  15,  16,  16,  17,  17,
                                     18,  18,  19,  19,  20,  21,  21,  22,  22,  23,  23,  24,  25,  25,  26,  27,
                                     27,  28,  29,  29,  30,  31,  31,  32,  33,  33,  34,  35,  36,  36,  37,  38,
                                     39,  40,  40,  41,  42,  43,  44,  45,  45,  46,  47,  48,  49,  50,  51,  52,
                                     53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,  65,  66,  67,  68,
                                     69,  70,  71,  72,  74,  75,  76,  77,  78,  79,  81,  82,  83,  84,  86,  87,
                                     88,  89,  91,  92,  93,  95,  96,  97,  99, 100, 101, 103, 104, 105, 107, 108,
                                    110, 111, 113, 114, 115, 117, 118, 120, 121, 123, 125, 126, 128, 129, 131, 132,
                                    134, 136, 137, 139, 140, 142, 144, 145, 147, 149, 151, 152, 154, 156, 158, 159,
                                    161, 163, 165, 166, 168, 170, 172, 174, 176, 178, 179, 181, 183, 185, 187, 189,
                                    191, 193, 195, 197, 199, 201, 203, 205, 207, 209, 211, 213, 215, 217, 220, 222,
                                    224, 226, 228, 230, 232, 235, 237, 239, 241, 244, 246, 248, 250, 253, 255,};

const int ledsPerStrip = 258;

// why multiply by 6? 2 bytes per colour??
DMAMEM int displayMemory[ledsPerStrip*6];
int drawingMemory[ledsPerStrip*6];

OctoWS2811 leds(ledsPerStrip, displayMemory, drawingMemory, WS2811_GRB | WS2811_800kHz);

//FIXME add timeout
uint8_t blocking_serial_read(unsigned long poll_interval) {
  while (!Serial.available()) {
    delay(poll_interval);
  }

  return Serial.read();
}

int process_data_frame() {
    // get header

    //FIXME fit both into one char?
    uint8_t strip_id = blocking_serial_read(1);
    
    //Serial.print("Frame received for pin ");
    //Serial.println(pin);
    
    if (strip_id > 7) {
      //Serial.println("Error: strip not found");
      return 0;
    }
    
    uint8_t pixel[3] = {0};
    int i = 0;

    uint8_t next_byte = blocking_serial_read(1);
    
    while (true) {
      if (next_byte == frame_start_char) {
        return -1;
        
      }
      else if (next_byte == frame_end_char) {
        if (iter++ % 2 == 0) {
          digitalWrite(onboard_led, currentState);
          currentState = !currentState;
          iter = 1;
        }
        
        return 0;
      }

      if (i <= ledsPerStrip*3) {
        int channelIndex = i%3;
        int pixelIndex = i/3;

        pixel[channelIndex] = next_byte;

        if (channelIndex == 2) {
          uint32_t val = gamma_table[pixel[1]] << 16 |
                         gamma_table[pixel[0]] << 8 |
                         gamma_table[pixel[2]];
      
          leds.setPixel(strip_id*ledsPerStrip + pixelIndex, val);
        }
        
        
      }

      i++;
      next_byte = blocking_serial_read(1);
    }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(onboard_led, OUTPUT);
  digitalWrite(onboard_led, HIGH);
  leds.begin();
}

void loop() {
  uint8_t start_char = blocking_serial_read(1);

  if (start_char == frame_start_char) {
    int result = -1;
    while (result == -1) { // returns -1 if a new frame started in the middle of a frame
      result = process_data_frame();
    }

    
    if (last_show + show_interval < millis()) {
      last_show = millis();
      leds.show();
    }
  }
}
