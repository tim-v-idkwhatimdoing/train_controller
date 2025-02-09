from itertools import cycle
from curio import sleep, Event
from bricknil import attach, start
from bricknil.hub import DuploTrainHub
from bricknil.sensor import DuploTrainMotor, DuploSpeedSensor, LED, DuploVisionSensor, DuploSpeaker, Button
from bricknil.const import Color
from collections import deque
import logging
import time
import json


"""   
    Pulled from bricknil/const.py : 
    black = 0 
    pink = 1
    purple = 2
    blue = 3
    light_blue = 4
    cyan = 5
    green = 6
    yellow = 7
    orange = 8
    red = 9
    white = 10
    none = 255
"""

@attach(DuploVisionSensor, name='vision_sensor', capabilities=[('sense_rgb', 10)])
@attach(LED, name='led')
@attach(DuploSpeedSensor, name='speed_sensor', capabilities=['sense_speed', 'sense_count'])
@attach(DuploTrainMotor, name='motor')
class Train(DuploTrainHub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pause = False        # Dont stop the train just pause
        self.waiting_for_movement = True
        self.speed = 0
        self.last_yellow_time = 0 # Track the last time color change happened
        self.last_red_time = 0    # Track the last time color change happened
        self.last_white_time = 0  # Track the last time color change happened
        self.last_blue_time = 0
        self.last_green_time = 0
        self.last_purple_time = 0
        self.last_orange_time = 0
        self.cooldown = 2

    #sounds = brake: 3, station: 5, water: 7, horn: 9, steam: 10

    async def speed_sensor_change(self):
        self.speed = self.speed_sensor.value[DuploSpeedSensor.capability.sense_speed]

    async def set_speed(self, target_speed, ramp_time):
        #target speed should always be positive
        # Change direction based on the current direction
        if self.direction == "reverse":
            new_speed = -target_speed
        else:
            new_speed = target_speed
        
        await self.motor.ramp_speed(new_speed, ramp_time)
        await sleep(.2)

    as


    async def run(self):
        while True: 
            if self.waiting_for_movement:
                self.message_info("Waiting for push...")
                await sleep(.08)
                if abs(self.speed) > 5:
                    self.waiting_for_movement = False
                    if self.speed < 0:
                        self.direction = "reverse"
                    else:
                        self.direction = "forward"
                    self.message_info(f"starting direction: {self.direction}, starting speed: {self.speed}")
                    await self.led.set_color(Color.blue)
                    self.speed = abs(self.speed)
                    await self.set_speed(self.speed,110)
                    self.message_info(f"Direction is: {self.direction}")
            elif not self.pause and abs(self.speed) < 10:
                await self.led.set_color(Color.green)
                self.message_info("Stopped, waiting for movement")
                self.waiting_for_movement = True
            await sleep(.1)

        self.message_info("Done")

async def system():
    hub = Train('train', False)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start(system)