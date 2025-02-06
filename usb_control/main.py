import curio
from curio import TaskGroup
from train import Train
from usb_controller import USBController
from bricknil import start

def handle_controller_input(buttons):
    print(f"Controller Input: {buttons}")  # Debugging: Show button presses

async def system():
    hub = Train('train', False)  # Create train instance
    return hub  # Ensure this returns the instance for Bricknil

async def run_bricknil():
    """Run Bricknil without blocking the Curio event loop."""
    await start(system)

async def main():
    usb_controller = USBController(handle_controller_input)

    async with TaskGroup() as group:
        await group.spawn(curio.run_in_thread, usb_controller.listen_for_input)  # Run USB listener in thread
        await group.spawn(run_bricknil)  # Run Bricknil concurrently

if __name__ == '__main__':
    curio.run(main())  # Ensure Curio properly runs the async main function
