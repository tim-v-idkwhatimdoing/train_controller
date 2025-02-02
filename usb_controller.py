import curio
import hid
import time

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


async def listen_to_usb_controller(train_controller):
    device = hid.device()
    device.open(VENDOR_ID, PRODUCT_ID)
    device.set_nonblocking(True)
    
    previous_data = None
    while True:
        data = device.read(64)
        
        # Only handle valid data
        if data:
            if data != previous_data:
                # Handle button presses
                print("Received data:", data)
                buttons_pressed = get_directional_buttons(data)
                train_controller.handle_button_input(buttons_pressed)  # Pass to train controller
                previous_data = data



