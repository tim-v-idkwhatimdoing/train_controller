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
import hid

VENDOR_ID = 3853  
PRODUCT_ID = 193  

# Define the button mapping, including the additional logic for byte values
BUTTON_MAP = {
    0: "Green",
    1: "Yellow",
    2: "Red",
    3: "Blue",
    4: "Left_Trigger",
    5: "Right_Trigger"
}

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

    def get_alt_buttons(byte_value):
        pressed_buttons = [name for bit, name in BUTTON_MAP.items() if byte_value & (1 << bit)]
        return pressed_buttons

    def get_directional_buttons(data):
        pressed_alt_buttons = get_alt_buttons(data[0])
        up_down = data[4]
        left_right = data[3]
    
        if up_down == 0:
            pressed_updown = "up"
        elif up_down == 255:
            pressed_updown = "down"
        else:
            pressed_updown = "neutral"
        if left_right == 0:
            pressed_leftright = "left"
        elif left_right == 255:
            pressed_leftright = "right"
        else:
            pressed_leftright = "neutral"

        button_pressed_combo = [pressed_updown, pressed_leftright, pressed_alt_buttons ]
        return button_pressed_combo

    async def listen_to_usb_controller():
        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
        device.set_nonblocking(True)
    
        previous_data = None
        while True:
            data = device.read(64)
        
        # Only handle valid data
        if data and data != previous_data:
            # Handle button presses
            previous_data = data
            buttons_pressed = get_directional_buttons(data)
            print(buttons_pressed)
            #return buttons_pressed

        time.sleep(0.08)

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
        await self.speaker.play_sound(DuploSpeaker.sounds[horn_sound])

    async def run(self):
        while True: 
            if self.waiting_for_movement:
                self.message_info("Waiting for push...")
                await sleep(.08)
                if abs(self.speed) > 5:
                    self.waiting_for_movement = False
                    if self.speed < 0:
                        self.direction = "reverse"
                        self.message_info("Starting off in reverse.")
                    else:
                        self.direction = "forward"
                    await self.led.set_color(Color.blue)
                    self.speed = abs(self.speed)
                    await self.set_speed(self.speed,110,"start")
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

        


