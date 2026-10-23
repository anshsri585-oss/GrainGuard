/*
  GrainGuard - Wokwi ESP32 + DHT22 Ambient Telemetry Simulation
  ------------------------------------------------------------
  Connects to Wokwi virtual Wi-Fi ("Wokwi-GUEST"), connects to HiveMQ public broker,
  and publishes ambient temperature and humidity as JSON to:
  Topic: "grainguard/demo/s01/ambient"

  Components:
  - ESP32 Development Board
  - DHT22 Temperature & Humidity Sensor (Data pin connected to GPIO 15)
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <ArduinoJson.h>

// Wi-Fi Configuration for Wokwi Simulation
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// HiveMQ Public Broker Configuration
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "grainguard/demo/s01/ambient";

const int DHT_PIN = 15;

WiFiClient espClient;
PubSubClient client(espClient);
DHTesp dht;

unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL = 5000; // Publish every 5 seconds

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected successfully!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to HiveMQ MQTT broker...");
    String clientId = "GrainGuard-ESP32-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed (rc=");
      Serial.print(client.state());
      Serial.println("). Retrying in 3 seconds...");
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.setup(DHT_PIN, DHTesp::DHT22);
  setup_wifi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastPublish > PUBLISH_INTERVAL) {
    lastPublish = now;

    TempAndHumidity data = dht.getTempAndHumidity();

    if (isnan(data.temperature) || isnan(data.humidity)) {
      Serial.println("Error reading from DHT22 sensor!");
      return;
    }

    // Format JSON payload matching GrainGuard mqtt_receiver.py
    StaticJsonDocument<200> doc;
    doc["stack_id"] = "S01";
    doc["sensor_type"] = "ambient_DHT22";
    doc["temperature_c"] = serialized(String(data.temperature, 2));
    doc["humidity_pct"] = serialized(String(data.humidity, 2));
    doc["data_source"] = "WOKWI_SIMULATION";

    char buffer[256];
    serializeJson(doc, buffer);

    Serial.print("Publishing to ");
    Serial.print(MQTT_TOPIC);
    Serial.print(": ");
    Serial.println(buffer);

    client.publish(MQTT_TOPIC, buffer);
  }
}
