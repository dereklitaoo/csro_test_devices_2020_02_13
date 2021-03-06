import paho.mqtt.client as mqtt
import threading
import json


class CSRO_Switch(threading.Thread):
    def __init__(self, mac, dev_type, num):
        threading.Thread.__init__(self)
        self.device_type = dev_type
        self.mac = mac
        self.channels = num
        self.client = mqtt.Client()
        self.switch_status = [0]

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe('csro/'+self.mac+"/" +
                              self.device_type+"/set/#", qos=0)
        for dev_index in range(0, self.channels):
            device = {
                "~": "csro/" + self.mac + "/" + self.device_type,
                "name": self.mac + "_"+self.device_type+"_"+str(dev_index),
                "uniq_id": self.mac + "_"+self.device_type+"_"+str(dev_index),
                "cmd_t": "~/set/" + str(dev_index),
                "pl_on": 1,
                "pl_off": 0,
                "stat_t": "~/state",
                "val_tpl": "{{value_json.state["+str(dev_index)+"]}}",
                "avty_t": "~/available",
                "dev": {
                    "ids": self.mac + "_"+self.device_type,
                    "name": self.mac + "_"+self.device_type,
                    "mf": "南京金星宇节能技术有限公司",
                    "mdl": self.device_type.upper(),
                    "sw": "2020_07_26"
                }
            }
            json_message = json.dumps(device)
            self.client.publish("csro/switch/"+self.mac+"_"+self.device_type +
                                "_"+str(dev_index)+"/config", json_message, retain=True)
        self.client.publish("csro/"+self.mac+"/" +
                            self.device_type+"/available", "online", retain=True)
        self.update_status()

    def on_message(self, client, userdata, msg):
        update = False
        for dev_index in range(0, self.channels):
            if str(msg.topic) == str("csro/" + self.mac + "/" + self.device_type+"/set/"+str(dev_index)):
                if msg.payload.decode('UTF-8') == "0":
                    self.switch_status[dev_index] = 0
                elif msg.payload.decode('UTF-8') == "1":
                    self.switch_status[dev_index] = 1
                update = True
            else:
                pass
        if update:
            self.update_status()

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.will_set("csro/"+self.mac+"/" +
                             self.device_type+"/available", "offline")
        self.client.connect('csro.net.cn', 1883, 60)
        self.client.loop_forever()

    def update_status(self):
        state = {
            "state": self.switch_status
        }
        state_message = json.dumps(state)
        self.client.publish("csro/"+self.mac+"/" +
                            self.device_type+"/state", state_message)
