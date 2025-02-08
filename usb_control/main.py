# main.py
import curio
import logging
from curio import TaskGroup
from train import Train
from usb_controller import USBController
from bricknil import start

# Create a queue for communication between threads/tasks
controller_queue = curio.Queue()

async def handle_controller_input(buttons):
    """Async function to handle controller input"""
    print(f"🎮 Adding to queue: {buttons}")
    print(f"Queue size before add: {controller_queue.qsize()}")
    await controller_queue.put(buttons)
    print(f"Queue size after add: {controller_queue.qsize()}")
    logging.info("Successfully queued buttons")

async def system():
    """Initialize the train system"""
    logging.info("Initializing train system")
    hub = Train('train', False)
    hub.controller_queue = controller_queue
    logging.info("Train system initialized with queue")
    return hub

async def monitor_queue():
    """Monitor the controller queue"""
    while True:
        try:
            print(f"📊 Queue Monitor - Size: {controller_queue.qsize()}")
            if not controller_queue.empty():
                print(f"📦 Next item: {controller_queue._queue[0]}")
        except Exception as e:
            logging.error(f"Error monitoring queue: {e}")
        await curio.sleep(1)

async def main():
    """Main async function coordinating all components"""
    try:
        # Initialize USB controller with async callback
        logging.info("Creating USB controller")
        usb_controller = USBController(handle_controller_input)
        
        # Start the USB controller
        logging.info("Starting USB controller")
        usb_controller.start()
        
        # Start queue monitor
        await curio.spawn(monitor_queue())
        
        # Give USB controller a moment to initialize
        await curio.sleep(1)
        
        logging.info("Starting Bricknil system")
        result = await start(system)
        
        while True:
            await curio.sleep(1)
            
    except Exception as e:
        logging.error(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    with curio.Kernel() as kernel:
        try:
            kernel.run(main, shutdown=True)
        except KeyboardInterrupt:
            logging.info("Shutting down gracefully...")
        except Exception as e:
            logging.error(f"Fatal error: {e}")


