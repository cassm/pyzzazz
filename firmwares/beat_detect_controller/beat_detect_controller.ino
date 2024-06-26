#include <DmxSimple.h>
#include <ADC.h>
ADC *adc = new ADC(); // adc object;

// Starting points for the audio DC offset, the lowest allowable audioRMSMax value,
// the starting threshold for a delta audio to be considered a beat, the minimum
// LED intensity, the target number of beats per second, the timestep between
// light setpoint updates, and the amount of hue change per second in degrees.

#define audioZeroStart 4096
#define audioRMSMaxStart 50
#define dThresholdStart 10
#define dThresholdMin 1
#define intensityMin 0.05
#define lightDecayPeriodStart 100
#define bpsTarget 6
#define timestep 10
#define hueStepPerSecond 60

// Flag to indicate that a beat has been detected. Beats are only
// recognized every DMX update (10ms default) which incidentally also
// manages debouncing to avoid confusing visual effects.

boolean beatdetected;

float intensity = intensityMin;

// Global variables to store filtered versions of signals and beat counts for
// auto-tuning. Also has decay periods for LED turn-off and the beat detection
// threshold which are varied slightly to adjust for different music genres.

float daudioRMSFiltered;
float dThreshold;
unsigned int beatCounts;
float beatCountsFiltered;
float lightDecayPeriod;
float audioRMSFiltered;
float audioRMSMax;
float audioZero;
float peakBeatVolume;

// Set up a timer for audio sampling rate. 44.1kHz is roughly 22us.
// In all honesty, this high of a speed is unnecessary to get excellent
// results, but your filter time constants will need changing to
// match different sampling rates.

elapsedMicros audioSamplingTimer;

// Set up a timer to periodically see how we're doing on getting a
// pleasant number of light flashes per beat analysis period.

elapsedMillis beatTimer;

// Set up a timer for actually sending updates to LED lights.

elapsedMillis sendtimer;

void setup() {// Setup for the DMX Simple Library. Pin 1 is the TX pin on the Teensy.
  // A better DMX library would allow me to send packets using the hardware
  // UART on that pin, but it works fine as is.
  
  
    adc->setResolution(16); // set bits of resolution
  
  // Configure input ADC for 13-bit mode, listed as the noise floor for the
  // Teensy 3.1 ADC. It would be fine to use 16 bits but I didn't see much
  // point between the noise in the ADC and the noise intrinsic in the audio
  // signal.

  // Set the audio zero level to ~4096 to start since it should be roughly
  // mid-scale, and sets start values for the threshold, max volume seen,
  // and light decay period. Once you get some info on what your board signal
  // levels look like this can be shifted to achieve a faster time to
  // when the board is working well.
  
  audioZero = audioZeroStart;
  audioRMSMax = audioRMSMaxStart;
  dThreshold = dThresholdStart;
  lightDecayPeriod = lightDecayPeriodStart;

  // Set the beat detected flag to false to start.
  
  beatdetected = false;

  // Starting parameters for filtered signals.
  
  daudioRMSFiltered = 0;
  beatCountsFiltered = 0;
  audioRMSFiltered = 0;

  // Initialize the peak beat volume storage.
  
  peakBeatVolume = 0;
}

void loop() {
  // This portion handles audio sampling and analysis.
  
  if (audioSamplingTimer > 22) { // No, really, 22us is roughly 44.1kHz! Coincidence?
    audioSamplingTimer = audioSamplingTimer - 22;
    
    // Input capacitively coupled, mid-scale centered audio signal.
    
    float audioSignal = adc->analogRead(A0);
  
    // Use exponential smoothing to capture the DC offset. This is using
    // the pure audio signal which should always have a stable DC offset
    // due to being capacitively coupled to the analog input.
    
    audioZero = 0.999999*audioZero + 0.000001*audioSignal;
  
    // Use the audioZero to calculate the RMS audio signal. This gives
    // the volume of the audio rather than an AC signal that is hard
    // to interpret. In past versions, abs() was used instead of RMS with
    // little loss of performance and faster calculation for use on
    // lower end hardware.
    
    float audioRMS = sqrt(pow(audioSignal - audioZero, 2));
    float oldaudioRMSFiltered = audioRMSFiltered;
    audioRMSFiltered = 0.99*audioRMSFiltered + 0.01*audioRMS;
  
    // If the audioRMSFiltered value exceeds the previously seen maximum,
    // set the audioRMSMax to the new value.
    
    if (audioRMSFiltered > audioRMSMax) audioRMSMax = audioRMSFiltered;
  
    // but every loop through, drag the audioRMSMax back towards zero so
    // that it doesn't only ever grow larger when it sees a volume increase.
    
    audioRMSMax = 0.99999*audioRMSMax + 0.00001*audioRMSMaxStart;

    // Next we need the rough derivitive of the piece, so we take the
    // current audioRMSFiltered value and subtract the immediately prior
    // sample. Very light exponential smoothing to avoid false pops.

    daudioRMSFiltered = 0.99*daudioRMSFiltered + 0.01*(audioRMSFiltered - oldaudioRMSFiltered);

    // and if the daudioRMSFIltered is higher than a threshold, indicate
    // beat detection.

    if (daudioRMSFiltered > dThreshold) {
      beatdetected = true;

      // The derivitive might exceed the threshold for several samples, so only
      // save the peak volume over the beat to set the light brightness peak during
      // that flash.
      
      peakBeatVolume = min(max(audioRMSFiltered/audioRMSMax, peakBeatVolume), 1);

      // Uncomment this to get debug values for tuning the audio signal chain.
      // However, it executes every audio sample, so disable during normal operation
      // to avoid taxing the processor too much.
      
      //Serial.println("Beat Detected with dAudio: " + String(daudioRMSFiltered) + " and amplitude " + String(peakBeatVolume));
    }
  }

  // This portion handles the actual DMX light updates.
  
  if (sendtimer >= timestep) {
    sendtimer = sendtimer - timestep;

    // Uncomment the below to get a stream of the detected audio DC offset level
    // useful for debugging, as well as the realtime audio RMS signal and recorded
    // maximum RMS value it is normalizing against.
    
    //Serial.println("Audio Zero: " + String(audioZero) + " Audio RMS: " + String(audioRMSFiltered) + " Normalized to Max of: " + String(audioRMSMax));

    // This section handles the case where a beat was detected.
    
    if (beatdetected) {
      beatdetected = false;
      
      // Increment the beatCounts by one, but only do this every DMX timestep to do
      // de-bouncing (i.e. don't count beats detected closer than 10ms apart as distinct).
      
      beatCounts++;

      // Set the light brightnesses to the normalized volume immediately.
      
      intensity = max(peakBeatVolume, intensity);

      // And reset the peak beat volume for the next beat detection event.
      peakBeatVolume = 0;
    }
    

    // But regardless, always be letting the light intensity drop down to the min level.
    // The decay speed varies based on song genre and the constants above.
    
    float timeConstant = min(timestep/lightDecayPeriod, 0.5);
    intensity = (1-timeConstant)*intensity + timeConstant*intensityMin;

    Serial.println(intensity*255);
    
    DmxSimple.write(1, 128);         // speed
    DmxSimple.write(2, 0);      // mode
    DmxSimple.write(3, intensity*255);     // audio level
    DmxSimple.write(4, 10); // flags
    DmxSimple.write(5, 128);             // R
    DmxSimple.write(6, 100);             // G
    DmxSimple.write(7, 0);             // B
  }

  // Finally, this does some automatic fudging of the beat detection threshold
  // and the time decay constant for the light to return to normal after a beat
  // to help compensate for quiet/classical/ambient music versus electronica.
  // The general idea is that if the threshold is pushed high because the song
  // has lots of light beats that would be too confusing to see if they were
  // all detected, the length of time of a light pulse up and back down is shorter
  // since the song overall sounds much more rhythmic and drummy.

  if (beatTimer > 1000) {
    beatTimer = beatTimer - 1000;
    beatCountsFiltered = max(0.1, 0.7*beatCountsFiltered + 0.3*(float)beatCounts);
    
    dThreshold = dThreshold + 0.05*(beatCountsFiltered - bpsTarget);
    dThreshold = max(dThreshold, dThresholdMin);
    
    lightDecayPeriod = max((dThresholdMin/dThreshold)*600, 100);

    // Debug information about the beat detection tuning, which is infrequent enough
    // that I left it uncommented here.
    
    //Serial.println("Detected " + String(beatCountsFiltered) + " BPS, target is " + String(bpsTarget) + ". New threshold is " + String(dThreshold) + ". Pulse decay TC is " + String(lightDecayPeriod));
    beatCounts = 0;
  }
}
