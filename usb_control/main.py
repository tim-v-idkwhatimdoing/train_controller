import curio
from curio import TaskGroup
from train import Train
from usb_controller import USBController
from bricknil import start

controller_queue = curio.Queue()  # Shared queue between threads

def handle_controller_input(buttons):
    #print(f"Controller Input: {buttons}")
    curio.run(controller_queue.put(buttons))  # Send input to queue (must be called from an async context)

async def process_controller_input():
    """ Continuously process controller input from the queue """
    while True:
        buttons = await controller_queue.get()  # Retrieve button input
        print(f"Processing: {buttons}")  # Example processing
        # Send this data to your Train instance if needed

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
