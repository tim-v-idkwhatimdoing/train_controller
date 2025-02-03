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
import curio

# Define the path to your JSON file
json_file_path2 = "actions.json"
# Read and load the JSON data into a dictionary
with open(json_file_path2, 'r') as file:
    actions_mapping = json.load(file)

@attach(DuploSpeaker, name='speaker')
@attach(LED, name='led')
@attach(DuploSpeedSensor, name='speed_sensor', capabilities=['sense_speed', 'sense_count'])
@attach(DuploTrainMotor, name='motor')
class Train(DuploTrainHub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pause = False        # Dont stop the train just pause
        self.waiting_for_movement = True
        self.speed = 0
        #self.direction = "forward"

    #sounds = brake: 3, station: 5, water: 7, horn: 9, steam: 10

    async def speed_sensor_change(self):
        self.speed = self.speed_sensor.value[DuploSpeedSensor.capability.sense_speed]

    async def set_speed(self, target_speed, ramp_time, description):
        #target speed should always be positive
        # Change direction based on the current direction
        self.message_info(f"Direction: {self.direction}, Speed: {target_speed} ")
        await self.motor.ramp_speed(target_speed, 250)
        await sleep(.5)

    async def make_sound(self, horn_sound):
        current_time = time.time()
        if not hasattr(self, "_last_sound_time"):
            self._last_sound_time = 0
        if current_time - self._last_sound_time > 0.5:  # Throttle to 0.5 seconds
             self._last_sound_time = current_time
        await self.speaker.play_sound(DuploSpeaker.sounds["horn"])

    async def run(self):
        while True:
            if self.waiting_for_movement:
                #print("Waiting for push...")
                await sleep(.08)
                if abs(self.speed) > 5:
                    self.waiting_for_movement = False
                    if self.speed < 0:
                        self.direction = "reverse"
                        print("Starting off in reverse.")
                    else:
                        self.direction = "forward"
                    await self.led.set_color(Color.blue)
                    await self.speaker.play_sound(DuploSpeaker.sounds["horn"])
                    self.speed = abs(75)
                    await self.set_speed(self.speed,110,"start")
            elif not self.pause and abs(self.speed) < 10:
                await self.led.set_color(Color.green)
                print("Stopped, waiting for movement")
                self.waiting_for_movement = True
            await sleep(.1)

        self.message_info("Done")

