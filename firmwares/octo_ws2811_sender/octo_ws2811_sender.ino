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

#define FPS 30

#define AWAITING_STRIP_ID 253
#define BETWEEN_FRAMES 252
#define MAX_STRIP_ID 7

uint64_t iter = 0;
bool currentLedState = 0;

const int ledsPerStrip = 200;

DMAMEM int displayMemory[ledsPerStrip*6];
int drawingMemory[ledsPerStrip*6];
int led_index = 0;
int pixel_index = 0;
uint8_t stripid = BETWEEN_FRAMES;

uint8_t current_frame[ledsPerStrip][3];

uint64_t last_render = 0;
uint64_t render_interval = 1000/FPS;

const uint8_t gamma_table[255] = {   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
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


OctoWS2811 leds(ledsPerStrip, displayMemory, drawingMemory, WS2811_RGB | WS2811_800kHz);

void setup() {
  // put your setup code here, to run once:
  pinMode(onboard_led, OUTPUT);
  digitalWrite(onboard_led, HIGH);
  leds.begin();
}

void loop() {
  while (Serial.available() && last_render + render_interval > millis()) {
    uint8_t symbol = Serial.read();
    
    if (symbol == frame_start_char) {
      led_index = 0;
      pixel_index = 0;
      stripid = AWAITING_STRIP_ID;
      digitalWrite(onboard_led, currentLedState);
      currentLedState = !currentLedState;
    }

    else if (symbol == frame_end_char) {
      led_index = 0;
      pixel_index = 0;
      stripid = BETWEEN_FRAMES;
    }
    
    else if (stripid == AWAITING_STRIP_ID) {
      stripid = symbol;
    }

    else if (stripid <= MAX_STRIP_ID and led_index < ledsPerStrip) {
      current_frame[led_index][pixel_index++] = symbol;
      
      if (pixel_index == 3) {
        leds.setPixel(stripid*ledsPerStrip + led_index, gamma_table[current_frame[led_index][0]], gamma_table[current_frame[led_index][1]], gamma_table[current_frame[led_index][2]]);
        pixel_index = 0;
        led_index++;
      }
    }
  }
  
  if (last_render + render_interval < millis()) {
    last_render = millis();
    leds.show();
  }
}
