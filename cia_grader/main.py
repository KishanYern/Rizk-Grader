import asyncio
import argparse
from canvas_bot import CanvasBot, SECTIONS


async def main():
    """
    The main function to create and run the CanvasBot.
    """
    parser = argparse.ArgumentParser(description='Upload QTI files to Canvas and generate grades')
    parser.add_argument('assignment', type=str, help='Assignment name (column header in Canvas CSV)')
    parser.add_argument('section', type=str, choices=['DS1', 'DS2', 'DSA'], 
                        help='Section: DS1, DS2, or DSA')
    parser.add_argument('--email', type=str, required=True, help='UH email address')
    parser.add_argument('--password', type=str, required=True, help='UH password')
    args = parser.parse_args()
        
    # Create an instance of the bot
    bot = CanvasBot(email=args.email, password=args.password)
    
    # Run the automation with the specified section and assignment
    await bot.run(section_code=args.section, assignment_name=args.assignment)


if __name__ == "__main__":
    # This block allows the script to be run directly from the command line.
    print("Starting the Canvas Bot...")
    print("""
Usage: python main.py <ASSIGNMENT> <SECTION> --email <EMAIL> --password <PASSWORD>

Examples:
  python main.py CIA1 DS1 --email user@uh.edu --password mypass
  python main.py CIA2 DSA --email user@uh.edu --password mypass
  
Sections:
  DS1 - COSC3337 18978 - Data Science I
  DS2 - COSC4337 20367 - Data Science II (placeholder)
  DSA - COSC2436 13434 - Programming and Data Structures
  
Make sure to place QTI .zip files in ./cias directory
""")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
    print("Canvas Bot has finished.")
