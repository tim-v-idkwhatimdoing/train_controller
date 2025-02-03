import curio
from curio import TaskGroup
from train import Train
from usb_controller import USBController
from bricknil import start

async def handle_controller_input(buttons):
    print(f"Controller Input: {buttons}")  # Debugging: Show button presses


# Define the system function for Bricknil (as required)
async def system():
    hub = Train('train', False)  # Create train instance
    return hub  # Ensure this returns the instance for Bricknil


async def main():
    async with TaskGroup() as group:
        
        print("Starting USB controller...")  # Debugging: Should appear next
        controller = USBController(handle_controller_input)
        await group.spawn(controller.listen_for_input)  # Start USB input listener

        print("Starting train system...")  # Debugging: Should appear first
        await group.spawn(start, system)  # Start Bricknil train system


if __name__ == '__main__':
    curio.run(main)
