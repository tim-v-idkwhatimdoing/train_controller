import hid
import time
import threading

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
        self.device = None
        self.running = False  # Initialize running state
        self.previous_data = None  # Store last read data

    def get_alt_buttons(self, byte_value):
        """ Decode button presses from byte value. """
        pressed_buttons = [name for bit, name in self.BUTTON_MAP.items() if byte_value & (1 << bit)]
        return pressed_buttons

    def get_directional_buttons(self, data):
        """ Extract directional and button inputs. """
        pressed_alt_buttons = self.get_alt_buttons(data[0])
        up_down = data[4]
        left_right = data[3]

        pressed_updown = "neutral"
        if up_down == 0:
            pressed_updown = "up"
        elif up_down == 255:
            pressed_updown = "down"

        pressed_leftright = "neutral"
        if left_right == 0:
            pressed_leftright = "left"
        elif left_right == 255:
            pressed_leftright = "right"

        return [pressed_updown, pressed_leftright, pressed_alt_buttons]

    def listen_for_input(self):
        """Run in a separate thread to avoid conflicts with Bricknil/Curio."""
        print("Initializing USB Controller in separate thread...")
        self.running = True  # Ensure running is set to True
        
        while self.running:
            try:
                if not self.device:
                    print("Attempting to open USB device...")
                    self.device = hid.device()
                    self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
                    self.device.set_nonblocking(True)

                data = self.device.read(64)
                if data and data != self.previous_data:
                    buttons_pressed = self.get_directional_buttons(data)
                    print(f"🟢 Processed Input: {buttons_pressed}")  # Debugging
                    self.previous_data = data

                    if self.callback:
                        self.callback(buttons_pressed)  # Direct call, no async needed
                
                time.sleep(0.08)  # Prevent flooding

            except KeyboardInterrupt:
                print("Keyboard interrupt detected, shutting down USB controller...")
                self.running = False  # Exit loop

            except Exception as e:
                print(f"Error reading from USB device: {e}")
                if self.device:
                    self.device.close()
                    self.device = None  # Reset device to allow re-initialization
                time.sleep(1)  # Wait before retrying

    def start(self):
        """Start the USB listener in a new thread."""
        if not self.running:
            thread = threading.Thread(target=self.listen_for_input, daemon=True)
            thread.start()
