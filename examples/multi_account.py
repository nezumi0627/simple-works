import asyncio
import os
import sys
import threading
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict

from dotenv import load_dotenv

from works.client import Works

# Load environment variables
load_dotenv()

# Set the appropriate event loop policy for Windows platform
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create cookie directory if it doesn't exist
COOKIE_DIR = Path("data")
COOKIE_DIR.mkdir(exist_ok=True)

# Account configurations
ACCOUNTS = [
    {
        "input_id": "example@1234",
        "password": "test@1234",
        "response": "Hi !! I'm multi-works :)",
    },
    {
        "input_id": "example2@1234",
        "password": "test@1234",
        "response": "Hi !! I'm multi-works 2 :)",
    },
]

# Domain and user settings from environment variables
domain_id = int(os.getenv("DOMAIN_ID", "0"))
user_no = int(os.getenv("USER_NO", "0"))
temp_message_id = int(os.getenv("TEMP_MESSAGE_ID", "0"))

# Store client instances
clients: Dict[str, Works] = {}


def handle_messages(account: dict) -> None:
    """Handle messages for a specific account."""
    try:
        client = Works(
            input_id=account["input_id"],
            password=account["password"],
            cookie_path=COOKIE_DIR,
        )
        clients[account["input_id"]] = client

        print(f"Started listening for messages on account: {account['input_id']}")

        for message in client.receive_messages(domain_id, user_no):
            content = message.get("content", "")
            channel_no = message.get("channelNo")

            if content == "!test":
                try:
                    response = client.send_message(
                        channel_no,
                        account["response"],
                        domain_id=domain_id,
                        user_no=user_no,
                        temp_message_id=temp_message_id,
                    )
                    print(f"Response from {account['input_id']}: {response}")
                except Exception as e:
                    print(f"Error sending message for {account['input_id']}: {e}")

    except Exception as e:
        print(f"Error in message handler for {account['input_id']}: {e}")


def main():
    """Main function to run multiple bot instances."""
    threads = []

    # Create and start a thread for each account
    for account in ACCOUNTS:
        thread = threading.Thread(
            target=handle_messages, args=(account,), name=f"Bot-{account['input_id']}"
        )
        thread.daemon = True  # Set as daemon thread
        threads.append(thread)
        thread.start()

    try:
        # Keep the main thread alive
        while True:
            # Check if all threads are alive
            alive_threads = [t for t in threads if t.is_alive()]
            if not alive_threads:
                print("All bot threads have stopped. Exiting...")
                break

            # Sleep to prevent CPU overuse
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))

    except KeyboardInterrupt:
        print("\nShutting down bots...")
        sys.exit(0)


if __name__ == "__main__":
    main()
