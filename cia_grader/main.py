import os
import asyncio
from canvas_bot import CanvasBot

# --- Configuration ---
# It's recommended to use environment variables for security.
# The script will fall back to the hardcoded values if environment variables are not set.
UH_EMAIL = os.getenv("UH_EMAIL", "EMAIL@CougarNet.UH.EDU")
UH_PASSWORD = os.getenv("UH_PASSWORD", "PASSWORD")


async def main():
    """
    The main function to create and run the CanvasBot.
    """
    if not UH_EMAIL or not UH_PASSWORD:
        print("Error: Please set UH_EMAIL and UH_PASSWORD environment variables or add them to the script.")
        return
        
    # Create an instance of the bot
    bot = CanvasBot(email=UH_EMAIL, password=UH_PASSWORD)
    
    # Run the automation
    await bot.run()


if __name__ == "__main__":
    # This block allows the script to be run directly from the command line.
    print("Starting the Canvas Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
    print("Canvas Bot has finished.")
