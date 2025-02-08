import hid
import time
import threading
import logging
import curio
    


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
        self._kernel = curio.Kernel()
        logging.info("USB Controller initialized")

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


    def _handle_input(self, buttons_pressed):
        #Schedules async execution properly
        if self.callback:
            try:
                self._kernel.run(self.callback(buttons_pressed))  # ✅ Runs the async function
            except Exception as e:
                logging.error(f"Error in callback: {e}")

    def listen_for_input(self):
        print("Initializing USB Controller in separate thread...")
        self.running = True

        while self.running:
            try:
                if not self.device:
                    print("Attempting to open USB device...")
                    self.device = hid.device()
                    self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
                    self.device.set_nonblocking(True)
                    logging.info("USB device opened successfully")

                data = self.device.read(64)
                if data and data != self.previous_data:
                    buttons_pressed = self.get_directional_buttons(data)
                    logging.info(f"USB Input detected: {buttons_pressed}")
                    self.previous_data = data
                    if self.callback:
                        try:
                            #curio.run_in_thread(self.callback, buttons_pressed)
                            #self._kernel.run(self.callback(buttons_pressed))  # ✅ This correctly runs an async functio
                            logging.info("Callback executed")
                            self._handle_input(buttons_pressed)
                        except Exception as e:
                            logging.error(f"Error in callback: {e}")
                        
                
                time.sleep(0.08)  # Prevent flooding


                
            except KeyboardInterrupt:
                print("Keyboard interrupt detected, shutting down USB controller...")
                self.running = False
            except Exception as e:
                print(f"Error reading from USB device: {e}")
                if self.device:
                    self.device.close()
                    self.device = None
                time.sleep(1)

    def start(self):
        """Start the USB listener in a new thread."""
        if not self.running:
            logging.info("Starting USB controller thread")
            thread = threading.Thread(target=self.listen_for_input, daemon=True)
            thread.start()
            logging.info("USB controller thread started")
