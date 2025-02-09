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



@attach(DuploSpeaker, name='speaker')
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

    # Function to check if each RGB component is within a given tolerance range
    def within_tolerance(self, color, target, tolerance):
        """
        Check if the RGB color is within the tolerance range of the target color.
        Args:
            color: The current (r, g, b) color value from the sensor.
            target: The target (r, g, b) color value to match.
            tolerance: The acceptable range of variation for each component.
        Returns:
            True if each component of color is within tolerance of target, else False.
        """
        return all(abs(c - t) <= tolerance for c, t in zip(color, target))

    async def set_speed(self, target_speed, ramp_time):
        #target speed should always be positive
        # Change direction based on the current direction
        if self.direction == "reverse":
            new_speed = -target_speed
        else:
            new_speed = target_speed
        
        await self.motor.ramp_speed(new_speed, ramp_time)
        await sleep(.2)

    async def vision_sensor_change(self):
        cap = DuploVisionSensor.capability
        color_rgb = self.vision_sensor.value[cap.sense_rgb]  # Get the RGB values from the sensor
        target_rgb = {'yellow':(1456,911,221),'white':(1578,1660,1520),'red':(1095,115,145), 'blue':(130,420,920),'green':(135,640,205), 'orange':(1336,266,183), 'purple':(196,174,400)} # The target RGB value to compare
        tolerance = 60  # Tolerance value for RGB components
        self.message_info(f"RGB Values: {color_rgb }.")
        for color_name, target in target_rgb.items():
            if self.within_tolerance(color_rgb, target, tolerance):
                if not self.waiting_for_movement:

                    current_time = time.time()
                    last_time_attr = f'last_{color_name}_time'    
                    
                    if (current_time - getattr(self, last_time_attr)) > self.cooldown:
                        self.message_info(f"detected color: {color_name}, {color_rgb}") 
                        setattr(self, last_time_attr, current_time)
                        self.message_info(f"{last_time_attr}: {getattr(self, last_time_attr)}")



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