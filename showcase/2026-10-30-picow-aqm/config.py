# config.py — copy to Pico W root and fill in your credentials
WIFI_SSID          = "YOUR_SSID"
WIFI_PASS          = "YOUR_WIFI_PASSWORD"

TELEGRAM_TOKEN     = "YOUR_BOT_TOKEN"          # @BotFather
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID"            # use @userinfobot

MQTT_BROKER        = "broker.hivemq.com"       # or self-hosted
MQTT_USER          = ""
MQTT_PASS          = ""
MQTT_TOPIC         = "sreconics/aqm/readings"

THINGSPEAK_WRITE_KEY = "YOUR_THINGSPEAK_KEY"   # channel field mapping:
                                               # field1=CO₂  field2=TVOC
                                               # field3=PM2.5 field4=Temp
                                               # field5=RH
