import hid
import time

class USBController:
    VENDOR_ID = 3853  
    PRODUCT_ID = 193  

    BUTTON_MAP = {
        0: "Green",
        1: "Yellow",
        2: "Red",
        3: "Blue",
        4: "Left_Trigger",
        5: "Right_Trigger"
    }

    def __init__(self, callback):
        self.callback = callback  # Function to handle button presses
        self.device = hid.device()

    def get_alt_buttons(self, byte_value):
        """ Decode button presses from byte value. """
        pressed_buttons = [name for bit, name in self.BUTTON_MAP.items() if byte_value & (1 << bit)]
        return pressed_buttons

    def get_directional_buttons(self, data):
        """ Extract directional and button inputs. """
        pressed_alt_buttons = self.get_alt_buttons(data[0])
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

        return [pressed_updown, pressed_leftright, pressed_alt_buttons]

    async def listen_for_input(self):
        """ Continuously read input from the USB controller. """
        try:
            self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
            print("✅ USB Controller Connected")

            self.device.set_nonblocking(True)
            previous_data = None

            while True:
                data = self.device.read(64)

                if data:
                    print(f"🟡 Raw Data Received: {data}")  # Debugging raw input data

                    if data != previous_data:
                        buttons_pressed = self.get_directional_buttons(data)
                        print(f"🟢 Processed Input: {buttons_pressed}")  # Show processed buttons
                        previous_data = data

                        if self.callback:
                            await self.callback(buttons_pressed)

                time.sleep(0.08)  # Slight delay to prevent flooding

        except Exception as e:
            print(f"❌ Error in USBController: {e}")

        finally:
            self.device.close()
            print("🔴 USB Controller Disconnected")
