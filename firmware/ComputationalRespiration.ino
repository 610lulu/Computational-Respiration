#include <Arduino.h>
#include <math.h>

// Computational Respiration — smooth ESP32 RGB prototype
// Baseline: ESP32 DevKit V1 / WROOM-32 + common-cathode RGB module.
const uint8_t PIN_R = 25;
const uint8_t PIN_G = 26;
const uint8_t PIN_B = 27;

// Set true for a common-anode module. Wire the common pin to 3V3 in that case.
const bool COMMON_ANODE = false;

const uint32_t UPDATE_MS = 15;
const float HEAT_SMOOTHING_PER_SECOND = 2.8f;
const float DEMO_STEP_SECONDS = 5.0f;

float targetHeat = 20.0f;
float currentHeat = 20.0f;
float breathPhase = 0.0f; // 0..1, continuous across load changes
uint32_t lastUpdateMs = 0;
uint32_t demoStartedMs = 0;
bool demoRunning = false;
String serialLine;

float lerpValue(float a, float b, float t) {
  return a + (b - a) * constrain(t, 0.0f, 1.0f);
}

void setRGB(int r, int g, int b) {
  r = constrain(r, 0, 255);
  g = constrain(g, 0, 255);
  b = constrain(b, 0, 255);
  if (COMMON_ANODE) {
    r = 255 - r;
    g = 255 - g;
    b = 255 - b;
  }
  analogWrite(PIN_R, r);
  analogWrite(PIN_G, g);
  analogWrite(PIN_B, b);
}

void setTarget(float value) {
  const float next = constrain(value, 0.0f, 100.0f);
  if (fabsf(next - targetHeat) < 0.05f) return;
  targetHeat = next;
  Serial.print("target=");
  Serial.print(targetHeat, 1);
  Serial.println("%");
}

void startDemo() {
  demoRunning = true;
  demoStartedMs = millis();
  Serial.println("demo: LOW -> MEDIUM -> HIGH -> continuous rise/fall");
}

void handleLine(String line) {
  line.trim();
  line.toLowerCase();
  if (line == "demo") {
    startDemo();
  } else if (line == "stop") {
    demoRunning = false;
    Serial.println("demo stopped; manual input enabled");
  } else if (line.length() > 0) {
    setTarget(line.toFloat());
    demoRunning = false;
  }
}

void readSerialNonBlocking() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '
' || c == '\r') {
      if (serialLine.length() > 0) {
        handleLine(serialLine);
        serialLine = "";
      }
    } else if (serialLine.length() < 24) {
      serialLine += c;
    }
  }
}

void updateDemo(float elapsed) {
  // 0–5s low, 5–10s medium, 10–15s high, then a smooth 15s triangle ramp.
  if (elapsed < DEMO_STEP_SECONDS) {
    setTarget(20.0f);
  } else if (elapsed < 2.0f * DEMO_STEP_SECONDS) {
    setTarget(55.0f);
  } else if (elapsed < 3.0f * DEMO_STEP_SECONDS) {
    setTarget(90.0f);
  } else {
    float rampTime = fmod(elapsed - 3.0f * DEMO_STEP_SECONDS, 15.0f);
    float ramp = rampTime <= 7.5f ? rampTime / 7.5f : 2.0f - rampTime / 7.5f;
    setTarget(20.0f + 70.0f * ramp);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(0);
  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  setRGB(0, 0, 0);
  lastUpdateMs = millis();
  Serial.println("Computational Respiration ready");
  Serial.println("Send 0-100, demo, or stop. Newline ending required.");
}

void loop() {
  readSerialNonBlocking();
  const uint32_t now = millis();
  const float dt = min((now - lastUpdateMs) / 1000.0f, 0.1f);
  lastUpdateMs = now;

  if (demoRunning) {
    updateDemo((now - demoStartedMs) / 1000.0f);
  }

  // Frame-rate-independent smoothing: alpha stays consistent if loop timing varies.
  const float alpha = 1.0f - expf(-HEAT_SMOOTHING_PER_SECOND * dt);
  currentHeat += (targetHeat - currentHeat) * alpha;

  const float heat = currentHeat / 100.0f;
  const float baseBrightness = lerpValue(0.25f, 0.90f, heat);
  const float period = lerpValue(6.0f, 1.5f, heat);
  const float minBreath = lerpValue(0.85f, 0.65f, heat);

  breathPhase += dt / period;
  if (breathPhase >= 1.0f) breathPhase -= floorf(breathPhase);
  const float wave = (sinf(2.0f * PI * breathPhase) + 1.0f) * 0.5f;
  const float breathingFactor = minBreath + (1.0f - minBreath) * wave;
  const float brightness = baseBrightness * breathingFactor;

  // Continuous warm-white -> orange-red colour mapping.
  const int r = (int)(255.0f * brightness);
  const int g = (int)(lerpValue(190.0f, 70.0f, heat) * brightness);
  const int b = (int)(lerpValue(120.0f, 20.0f, heat) * brightness);
  setRGB(r, g, b);
  delay(UPDATE_MS);
}



