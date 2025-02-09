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

# Define the path to your JSON file
json_file_path2 = "actions.json"
# Read and load the JSON data into a dictionary
with open(json_file_path2, 'r') as file:
    actions_mapping = json.load(file)

@attach(DuploSpeaker, name='speaker')
@attach(DuploVisionSensor, name='vision_sensor', capabilities=[('sense_rgb', 10)])
@attach(LED, name='led')
@attach(DuploSpeedSensor, name='speed_sensor', capabilities=['sense_speed', 'sense_count'])
@attach(DuploTrainMotor, name='motor')
class Train(DuploTrainHub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_yellow_time = 0 # Track the last time color change happened
        self.last_red_time = 0    # Track the last time color change happened
        self.last_white_time = 0  # Track the last time color change happened
        self.last_blue_time = 0
        self.last_green_time = 0
        self.last_purple_time = 0
        self.last_orange_time = 0
        self.pause = False        # Dont stop the train just pause
        self.waiting_for_movement = True
        self.speed = 0
        self.direction = "forward"

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

    async def set_speed(self, target_speed, ramp_time, description):
        #target speed should always be positive
        if self.direction == "reverse":
            target_speed = -target_speed
        else:
            target_speed = target_speed
        await self.motor.ramp_speed(target_speed, ramp_time)
        await sleep(1)

    async def vision_sensor_change(self):
        cap = DuploVisionSensor.capability
        color_rgb = self.vision_sensor.value[cap.sense_rgb]  # Get the RGB values from the sensor134, 643, 206
        target_rgb = {'yellow':(1456,911,221),'white':(1578,1660,1520),'red':(1095,115,145), 'blue':(130,420,920),'green':(135,640,205), 'orange':(1336,266,183), 'purple':(196,174,400)} # The target RGB value to compare
        tolerance = 60  # Tolerance value for RGB components
        #self.message_info(f"RGB Values: {color_rgb }.")
        for color_name, target in target_rgb.items():
            #self.message(f"{color_name}: {target} + actual: {color_rgb}")
            if self.within_tolerance(color_rgb, target, tolerance):
                #self.message_info(f"detected color: {color_name}")
                if not self.waiting_for_movement:
                    await self.action_color(color_name)

        return None  # No color detected    

    async def action_color(self,detected_color):
        json_file_path = 'color_mapping.json'
        with open(json_file_path, 'r') as file:
            color_actions = json.load(file)
        last_time_attr = f'last_{detected_color}_time'
        self.message_info(f"just saw color: {detected_color}")
        mapping = color_actions.get(detected_color, {})
        if mapping is None:
            self.message_info(f"No mapping found for color: {detected_color}")
            return  # Exit early

        action_to_take = actions_mapping.get(mapping)
        if action_to_take is None:
            self.message_info(f"No action found for mapping: {mapping}")
            return  # Exit early

        action_to_take = actions_mapping.get(mapping,{})
        current_time = time.time()


        if (current_time - getattr(self, last_time_attr)) > action_to_take["cooldown"]: 
            setattr(self, last_time_attr, current_time)
            print()
            self.message_info(f"got past the cooldown part. Doing: {action_to_take}")
            if action_to_take["action"] == "change_direction":
                self.pause = True
                await self.speaker.play_sound(DuploSpeaker.sounds["brake"])
                await self.set_speed(0,150,"Reverse stop")
                await self.led.set_color(Color.red)
                await sleep(2)
                if self.direction == "forward":
                    self.direction = "reverse"
                elif self.direction == "reverse":
                    self.direction = "forward"
                await self.led.set_color(Color.green)
                await self.set_speed(75,500,"direction-change")
                self.pause = False
                await self.speaker.play_sound(DuploSpeaker.sounds["steam"])
                self.message_info(f"pause status: {self.pause}")
                await sleep(.5)


            if action_to_take["action"] == "stop":
                await self.speaker.play_sound(DuploSpeaker.sounds["brake"])
                await self.led.set_color(Color.red)
                await self.set_speed(0,150,"stop")
                waiting_for_movement = True
                await sleep(.8)
                await self.speaker.play_sound(DuploSpeaker.sounds["station"])

            if action_to_take["action"] == "pause":
                await self.led.set_color(Color.red)
                self.pause = True
                await self.set_speed(0,150,"stop")
                await sleep(2.5)
                await self.led.set_color(Color.green)
                await self.set_speed(75, 2000, "slow-ramp")
                await sleep(3)
                self.pause = False

            if action_to_take["action"] == "max_speed":
                await self.led.set_color(Color.green)
                await self.speaker.play_sound(DuploSpeaker.sounds["horn"])
                await self.set_speed(100,250,"increase")
                    
            if action_to_take["action"] == "slow_speed":
                await self.led.set_color(Color.yellow)
                await self.speaker.play_sound(DuploSpeaker.sounds["brake"])
                if self.speed > 70:
                    await self.set_speed(50,150, "decrease")
                if self.speed <= 70 and self.speed > 40:
                    new_speed = self.speed - 20
                    await self.set_speed(new_speed,100,"decrease")
                else:
                    pass

            if action_to_take["action"] == "small_increase":
                await self.led.set_color(Color.green)
                await self.speaker.play_sound(DuploSpeaker.sounds["horn"])
                if self.speed <= 90:
                    new_speed = self.speed - action_to_take["increase_amount"]
                    await self.set_speed(new_speed,action_to_take["ramp_speed"],"increase")
                else: 
                    pass

            if action_to_take["action"] == "small_decrease":
                await self.speaker.play_sound(DuploSpeaker.sounds["brake"])
                await self.led.set_color(Color.yellow)
                if self.speed >= 25:
                    new_speed = self.speed - action_to_take["decrease_amount"]
                    await self.set_speed(new_speed,action_to_take["ramp_speed"],"decrease")
                else: 
                    pass

            if action_to_take["action"] == "light_and_sound":
                iterations = action_to_take["iterations"]
                await self.speaker.play_sound(DuploSpeaker.sounds["station"])
                for _ in range(iterations):
                    for led_color in ["red","white","blue","green","yellow"]:
                        await self.led.set_color(Color[led_color])  
                        await sleep(.2)

        await sleep(.2)

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
                    await self.led.set_color(Color.blue)
                    await self.set_speed(100,110,"start")
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