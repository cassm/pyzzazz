#include <Redis.h>
#include <Adafruit_NeoPixel.h>
#include "ESP8266TimerInterrupt.h"
#include "gamma.h"

/*****************************************
******** SET THIS FOR EACH UNIT **********
******************************************/

#define PSU_WATTS 25

/*****************************************
*****************************************/

#ifdef __AVR__
 #include <avr/power.h> // Required for 16 MHz Adafruit Trinket
#endif

#define LED_PIN D1

#define NUM_LEDS PSU_WATTS*6
#define NUM_RGBW_LEDS NUM_LEDS*0.75

const double watts_per_rgb_bit = 0.00015;
const double watts_per_w_bit = 0.00029;

// this sketch will build for the ESP8266 or ESP32 platform
#ifdef HAL_ESP32_HAL_H_ // ESP32
#include <WiFiClient.h>
#include <WiFi.h>
#else
#ifdef CORE_ESP8266_FEATURES_H // ESP8266
#include <ESP8266WiFi.h>
#endif
#endif

enum COLOUR_MODE {
    COLOUR_MODE_RGB,
    COLOUR_MODE_RGBW
};

COLOUR_MODE CURRENT_COLOUR_MODE = COLOUR_MODE_RGB;

#define WIFI_SSID "pyzzazz-net"
#define WIFI_PASSWORD "every-colour-illuminate"

#define REDIS_ADDR "192.168.0.3"
#define REDIS_PORT 6379
#define REDIS_PASSWORD "9p7ytGYqG"

#define MAX_BACKOFF 300000 // 5 minutes

#define USING_TIM_DIV16 // use medium timer accuracy

ESP8266Timer ITimer;

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

String MAC_ADDR = "";
String leds_channel = "";
String cmd_channel = "";

uint8_t colours[NUM_LEDS][3];

bool PINGED = false;
uint64_t last_ping = 0;

void forceReset(void) {
    Serial.println("Restarting...");
    ESP.restart();
}

void unping() {
    //Serial.println("UNPING");
    ITimer.stopTimer();
    PINGED = false;
    setPixelsFromBuffer();
    pixels.show();
}

void power_limit() {
    double total_watts = 0;

    for (int led = 0; led < NUM_LEDS; led++) {
        for (int ch = 0; ch < 3; ch++) {
            int channel_index = led*3 + ch;
            
            if (CURRENT_COLOUR_MODE == COLOUR_MODE_RGBW && (channel_index % 4 == 0)) {
               total_watts += watts_per_w_bit*colours[led][ch];
            }
            else {
               total_watts += watts_per_rgb_bit*colours[led][ch];
            }
        }
    }

    if (total_watts > PSU_WATTS) {
        double scaling_factor = total_watts / PSU_WATTS;

        for (int led = 0; led < NUM_LEDS; led++) {
            for (int ch = 0; ch < 3; ch++) {
                colours[led][ch] *= scaling_factor;
            }
        }
    }
}

void setup()
{
  Serial.begin(115200);
  Serial.println();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to the WiFi");

  
  ITimer.setInterval(3000000L, unping);
  ITimer.stopTimer();

  MAC_ADDR = WiFi.macAddress();
  MAC_ADDR.replace(":", "."); // swap out colons to make redis namespace more legible

  const String client_channel_prefix = "pyzzazz:clients:" + MAC_ADDR + ":";
  leds_channel = client_channel_prefix + "leds";
  cmd_channel = client_channel_prefix + "cmd";

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  
  pixels.begin();

  auto backoffCounter = -1;
  auto resetBackoffCounter = [&]() {
    backoffCounter = 0;
  };

  resetBackoffCounter();
  while (subscriberLoop(resetBackoffCounter))
  {
    auto curDelay = min((1000 * (int)pow(2, backoffCounter)), MAX_BACKOFF);

    if (curDelay != MAX_BACKOFF)
    {
      ++backoffCounter;
    }

    Serial.printf("Waiting %lds to reconnect...\n", curDelay / 1000);
    delay(curDelay);
  }


  Serial.printf("Done!\n");
  forceReset();

}

void msgCallback (String channel, String msg) {
  //Serial.printf("Message on channel '%s': \"%s\"\n", channel.c_str(), msg.c_str());

  if (channel == "pyzzazz:clients:cmd" || channel == cmd_channel.c_str())
  {
    Serial.println("Got message on cmd channel");
    Serial.println("::" + msg + "::");
    if (msg == "PING") {
      pong();
    }
    else if (msg == "CLEAR") {
      clearPixels();
    }
    else if (msg == "COLOUR_MODE_RGB") {
        Serial.println("Setting colour mode to RGB");
        CURRENT_COLOUR_MODE = COLOUR_MODE_RGB;
    }
    else if (msg == "COLOUR_MODE_RGBW") {
        Serial.println("Setting colour mode to RGBW");
        CURRENT_COLOUR_MODE = COLOUR_MODE_RGBW;
    }
    else if (msg == "RESET") {
        forceReset();
    }
  }
  else if (channel == leds_channel.c_str())
  {
    updateColours(msg);
    
    if (!PINGED) {
      setPixelsFromBuffer();
    }
    pixels.show();
  }
}

// returning 'true' indicates the failure was retryable; false is fatal
bool subscriberLoop(std::function<void(void)> resetBackoffCounter)
{
  WiFiClient redisConn;
  if (!redisConn.connect(REDIS_ADDR, REDIS_PORT))
  {
    Serial.println("Failed to connect to the Redis server!");
    return true;
  }

  Redis redis(redisConn);
  auto connRet = redis.authenticate(REDIS_PASSWORD);
  if (connRet == RedisSuccess)
  {
    Serial.println("Primary client connected to the Redis server!");
  }
  else
  {
    Serial.printf("Primary client failed to authenticate to the Redis server! Errno: %d\n", (int)connRet);
    return false;
  }

  // do not overwrite existing client node config
  String clientResult = redis.hget("pyzzazz:clients", MAC_ADDR.c_str());
  if (clientResult == "") {
    redis.hset("pyzzazz:clients", MAC_ADDR.c_str(), "unassigned");
  }

  // get colour mode if available  
  clientResult = redis.hget("pyzzazz:colourModes", MAC_ADDR.c_str());
  if (clientResult == "") {
    redis.hset("pyzzazz:colourModes", MAC_ADDR.c_str(), "COLOUR_MODE_RGB");
  }
  else if (clientResult == "COLOUR_MODE_RGBW") {
    CURRENT_COLOUR_MODE = COLOUR_MODE_RGBW;
  }
  
  Serial.println("subscribing to channel " + leds_channel);
  Serial.println("subscribing to channel " + cmd_channel);
  Serial.println("subscribing to channel clients:cmd");
  redis.subscribe(leds_channel.c_str());
  redis.subscribe(cmd_channel.c_str());
  redis.subscribe("pyzzazz:clients:cmd");

  Serial.println("Listening...");
  resetBackoffCounter();

  RedisSubscribeResult subRv = redis.startSubscribing(
                                 msgCallback,
  [ = ](Redis * redisInst, RedisMessageError err) {
    Serial.printf("Subscription error! '%d'\n", err);
  });

  redisConn.stop();
  Serial.printf("Connection closed! (%d)\n", subRv);
  return subRv == RedisSubscribeServerDisconnected; // server disconnect is retryable, everything else is fatal
}

void updateColours(String colourString) {
    const int numLeds = colourString.length() / 9;
    const int maxLeds = CURRENT_COLOUR_MODE == COLOUR_MODE_RGB ? NUM_LEDS : NUM_RGBW_LEDS;
    
    for (int led = 0; led < min(maxLeds, numLeds); led++) {
      uint8_t ledVal[3];
      
      for (int ch = 0; ch < 3; ch++) {
        const String hex = colourString.substring(led * 9 + ch * 3, led * 9 + ch * 3 + 3);
        ledVal[ch] = (uint8_t)strtol(hex.c_str(), NULL, 16);
      }

      if (CURRENT_COLOUR_MODE == COLOUR_MODE_RGB) {
        for (int i = 0; i < 3; i++) {
          colours[led][i] = gamma_table[ledVal[i]];
        }
      }
      else {
        uint8_t wVal = min(ledVal[0], min(ledVal[1], ledVal[2]));

        int base_channel = led*4;
        for (int i = 0; i < 3; i++) {
          colours[(base_channel+i) / 3][(base_channel+i) % 3] = gamma_table[ledVal[i] - wVal];
        }
            
        colours[(base_channel+3) / 3][(base_channel+3) % 3] = gamma_table[wVal];
      }
    }
}

void setPixelsFromBuffer() {
  pixels.clear();
  for (int led = 0; led < NUM_LEDS; led++) {
    pixels.setPixelColor(led, pixels.Color(
      colours[led][1],
      colours[led][0],
      colours[led][2]
    ));
  }
}

void pong() {
  Serial.println("PING");
  if (!PINGED) {
    for (int led = 0; led < NUM_LEDS; led++) {
      pixels.setPixelColor(led, pixels.Color(128, 128, 128));
    }
    pixels.show();
    PINGED=true;
    ITimer.restartTimer();
  }
}

void clearPixels() {
  for (int led = 0; led < NUM_LEDS; led++) {
    pixels.setPixelColor(led, pixels.Color(0, 0, 0));
  }
  if (!PINGED) {
    setPixelsFromBuffer();
    pixels.show();
  }
}
void loop() {}
