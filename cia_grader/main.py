import os
import asyncio
import argparse
from canvas_bot import CanvasBot, SECTIONS

# --- Configuration ---
# It's recommended to use environment variables for security.
UH_EMAIL = os.getenv("UH_EMAIL", "EMAIL@CougarNet.UH.EDU")
UH_PASSWORD = os.getenv("UH_PASSWORD", "PASSWORD")


async def main():
    """
    The main function to create and run the CanvasBot.
    """
    parser = argparse.ArgumentParser(description='Upload QTI files to Canvas and generate grades')
    parser.add_argument('assignment', type=str, help='Assignment name (column header in Canvas CSV)')
    parser.add_argument('section', type=str, choices=['DS1', 'DS2', 'DSA'], 
                        help='Section: DS1 (Data Science I), DS2 (Data Science II), or DSA (Data Structures)')
    args = parser.parse_args()
    
    if not UH_EMAIL or not UH_PASSWORD or "EMAIL@" in UH_EMAIL:
        print("Error: Please set UH_EMAIL and UH_PASSWORD environment variables or update the script.")
        return
        
    # Create an instance of the bot
    bot = CanvasBot(email=UH_EMAIL, password=UH_PASSWORD)
    
    # Run the automation with the specified section and assignment
    await bot.run(section_code=args.section, assignment_name=args.assignment)


if __name__ == "__main__":
    # This block allows the script to be run directly from the command line.
    print("Starting the Canvas Bot...")
    print("""
Usage: python main.py <ASSIGNMENT_NAME> <SECTION>

Examples:
  python main.py CIA1 DS1    # Upload CIAs for Data Science I
  python main.py CIA2 DSA    # Upload CIAs for Data Structures
  
Sections:
  DS1 - COSC3337 18978 - Data Science I
  DS2 - COSC4337 20367 - Data Science II (placeholder)
  DSA - COSC2436 13434 - Programming and Data Structures
  
Make sure to:
1. Place QTI .zip files in ./cias directory
2. Set UH_EMAIL and UH_PASSWORD environment variables
""")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
    print("Canvas Bot has finished.")
