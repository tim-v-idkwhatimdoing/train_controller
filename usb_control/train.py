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

#sounds = brake: 3, station: 5, water: 7, horn: 9, steam: 10
# Train class (train.py)
@attach(DuploSpeaker, name='speaker')
@attach(LED, name='led')
@attach(DuploSpeedSensor, name='speed_sensor', capabilities=['sense_speed', 'sense_count'])
@attach(DuploTrainMotor, name='motor')
class Train(DuploTrainHub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller_queue = None
        self.pause = False
        self.waiting_for_movement = True
        self.speed = 0
        self.direction = "forward"
        self.last_command_time = time.time()
        self.command_cooldown = 0.1
        self.color_list = ["black", "white", "red", "green", "pink", "blue", "yellow", "purple", "light_blue", "orange", "cyan"]
        self.color_iterator = 0 
    async def process_queue_item(self, buttons):
        """Process a single queue item"""
        try:
            current_time = time.time()
            if current_time - self.last_command_time < self.command_cooldown:
                return
            
            self.last_command_time = current_time
            print(f"Train processing: {buttons}")
            direction = buttons[0]
            turn = buttons[1]
            alt_buttons = buttons[2]

            if direction == "up":
                self.direction = "forward"
                self.waiting_for_movement = False
                self.pause = False
                await self.set_speed(100, 300, "manual control")
                print("▶️ Forward")

            elif direction == "down":
                self.direction = "reverse"
                self.waiting_for_movement = False
                self.pause = False
                await self.set_speed(100, 300, "manual control")

            elif direction == "neutral" and not self.waiting_for_movement:
                await self.set_speed(0, 250, "manual control")
                print("⏹️ Stop")
           
            if turn == "right":
                self.color_iterator += 1
                if self.color_iterator > 10:
                    self.color_iterator = 0
                color_change = self.color_list[self.color_iterator]
                await self.led.set_color(Color[color_change])
                print(f"Color changed to: {color_change}")

            if turn == "left":
                self.color_iterator -= 1
                if self.color_iterator < 0:
                    self.color_iterator = 10
                color_change = self.color_list[self.color_iterator]
                await self.led.set_color(Color[color_change])
                print(f"Color changed to: {color_change}")

            if isinstance(alt_buttons, list) and alt_buttons:
                for button in alt_buttons:
                    #print(f"In process button queue action on: {button}")
                    if button == "Red":
                        await self.make_sound("brake")
                        await self.set_speed(0, 150, "emergency stop")
                        print("🛑 Emergency Stop")
                    elif button == "Blue":
                        await self.make_sound("horn")
                        print("📢 Horn")
                    elif button == "Green":
                        await self.make_sound("steam")
                    elif button == "Yellow":
                        await self.make_sound("station")

        except Exception as e:
            logging.error(f"Error processing queue item: {e}")
            print(f"❌ Process error: {e}")

    async def speed_sensor_change(self):
        self.speed = self.speed_sensor.value[DuploSpeedSensor.capability.sense_speed]

    async def set_speed(self, target_speed, ramp_time, description):
        #target speed should always be positive
        if self.direction == "reverse":
            new_speed = -target_speed
        else:
            new_speed = target_speed
        self.message_info(f"Direction: {self.direction}, Speed: {new_speed}, ")
        await self.motor.ramp_speed(new_speed, ramp_time)
        await sleep(.1)

    async def make_sound(self, horn_sound):
        current_time = time.time()
        if not hasattr(self, "_last_sound_time"):
            self._last_sound_time = 0
        if current_time - self._last_sound_time > 1 :  # Throttle to 1 second
            self._last_sound_time = current_time
            await self.speaker.play_sound(DuploSpeaker.sounds[horn_sound])

    async def run(self):
        """Main run loop"""
        print("🚂 Train starting...")
        
        while True:
            try:
                # Process any queued commands
                if self.controller_queue and not self.controller_queue.empty():
                    buttons = await self.controller_queue.get()
                    print(f"📥 Got from queue: {buttons}")
                    await self.process_queue_item(buttons)
                
                # Handle movement detection
                if self.waiting_for_movement:
                    if abs(self.speed) > 5:
                        self.waiting_for_movement = False
                        if self.speed < 0:
                            self.direction = "reverse"
                        else:
                            self.direction = "forward"
                        await self.set_speed(100, 110, "start")
                        print(f"Starting, direction: {self.direction}")
                elif not self.pause and abs(self.speed) < 10:
                    print("⏸️ Stopped, waiting for movement")
                    self.waiting_for_movement = True
                
                await curio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error in run loop: {e}")
                print(f"❌ Run error: {e}")
                await curio.sleep(1)
