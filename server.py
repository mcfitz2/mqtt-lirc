from lirconian import UnixDomainSocketLirconian as LIRC
import paho.mqtt.client as mqtt
import os
import json
import logging
import sys

config = {}
if os.path.exists("config.json"):
    try:
        with open("config.json", 'r') as f:
            config.update(json.load(f))
    except Exception as e:
        print("Error loading config file")
        print(e)
        sys.exit(1)
try:
	os.makedirs(config['log_path'])
except FileExistsError:
	pass
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
fileHandler = logging.FileHandler("{0}/{1}.log".format(config['log_path'], 'mqtt-lirc'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

lirc = LIRC()
def parse_topic(topic):
    try:
        start, remote, button = topic.split("/")
        if start == config.get("prefix"):
            return remote, button
        return None, None
    except:
        return None, None
def on_connect(mqttc, obj, flags, rc):
    logging.info("rc: " + str(rc))
    logging.info("connected")
    mqttc.subscribe(config["prefix"]+"/+/+", 0)

def on_message(mqttc, obj, msg):
    logging.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    remote, button = parse_topic(msg.topic)
    if remote and button:
        lirc.send_ir_command(remote, button, 1)

def on_publish(mqttc, obj, mid):
    logging.info("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    logging.info("Subscribed: " + str(obj) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    logging.info(string)

def on_disconnect(client, userdata, rc):
    m = "disconnecting reason: " + str(rc)
    logging.info(m)
    logging.info('trying to connect')
    client.connect(config["host"], config["port"], 60)

# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect
# Uncomment to enable debug messages
# mqttc.on_log = on_log
if config.get("username") and config.get("password"):
    mqttc.username_pw_set(config.get("username"), password=config.get("password"))
print(config["prefix"]+"/+/+")

mqttc.connect(config["host"], config["port"], 60)
mqttc.subscribe(config["prefix"]+"/+/+", 0)
mqttc.loop_forever()
