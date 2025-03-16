import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union, Tuple

class TelegramPickupBot:
    def __init__(self, token: str, chat_id: str):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Telegram bot API token
            chat_id: ID of the group chat where announcements will be posted
        """
        self.TOKEN = token
        self.chat_id = chat_id
        self.message_id: Optional[int] = None
        self.new_users: Dict[str, Dict[str, Any]] = {}
    
    def reset_bot_completely(self) -> None:
        """Reset the bot by clearing local data and pending updates."""
        self.clear_local_user_data()
        self.reset_bot_webhook()
        print("Bot has been reset completely")
    
    def clear_local_user_data(self) -> bool:
        """Clear any locally stored user data."""
        self.new_users = {}
        print("Local user data cleared")
        
        if os.path.exists("user_data.json"):
            os.remove("user_data.json")
            print("User data file removed")
        
        return True
    
    def reset_bot_webhook(self) -> bool:
        """Remove the webhook to ensure no old updates are processed."""
        url = f"https://api.telegram.org/bot{self.TOKEN}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url)
        result = response.json()
        
        if result["ok"]:
            print("Webhook deleted and pending updates cleared")
            return True
        else:
            print(f"Failed to reset webhook: {result}")
            return False
        
    def schedule_message_deletion(self, chat_id: Union[str, int], message_id: int, delay_seconds: int = 2) -> None:
        """
        Schedule a message for deletion after specified delay.
        
        Args:
            chat_id: Chat ID where the message was sent
            message_id: ID of the message to delete
            delay_seconds: Time in seconds after which to delete the message (default: 24 hours)
        """
        import threading
        
        def delete_after_delay():
            time.sleep(delay_seconds)
            url = f"https://api.telegram.org/bot{self.TOKEN}/deleteMessage"
            params = {
                "chat_id": chat_id,
                "message_id": message_id
            }
            response = requests.get(url, params=params)
            if response.json()["ok"]:
                print(f"Auto-deleted message {message_id} in chat {chat_id}")
            else:
                print(f"Failed to auto-delete message {message_id} in chat {chat_id}")
        
        thread = threading.Thread(target=delete_after_delay)
        thread.daemon = True
        thread.start()
        print(f"Scheduled message {message_id} for deletion in {delay_seconds} seconds")
    
    def send_message_emergency_group(self, location: str, date: str, pick_up_time: str) -> Optional[int]:
        """
        Send a message to the emergency group with pickup details.
        
        Args:
            location: Pickup location
            date: Date of the pickup
            pick_up_time: Time of the pickup
            
        Returns:
            Message ID if successful, None otherwise
        """
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "CONFIRM PICK-UP! Click and START.",
                        "url": f"https://t.me/skat_cards_distribution_bot"
                    }
                ]
            ]
        }
        
        # Convert the keyboard to JSON string
        reply_markup = json.dumps(keyboard)
        
        # Calculate response deadline (1 hour from now)
        response_time = time.strftime('%H:%M', time.localtime(time.time() + 3600))
        
        # Message text
        message = (
            f"Hey Foodsavers, we have a request for an Event Pick Up.\n\n"
            f"<b>Where:</b> <i>{location}</i> \n"
            f"<b>When:</b> <i>{date}</i> \n"
            f"<b>Time:</b> <i>{pick_up_time}</i> \n\n"
            f"You have time until {response_time} to response. \n"
            f"If you can pick up:"
        )
        
        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage"
        params = {
            "chat_id": self.chat_id, 
            "text": message, 
            "reply_markup": reply_markup, 
            "parse_mode": "HTML"
        }
        response = requests.get(url, params=params)
        
        # Get the message ID from the response for later deletion
        result = response.json()
        if result["ok"]:
            self.message_id = result["result"]["message_id"]
            return self.message_id
        else:
            print(f"Error: {result}")
            return None
    
    def get_bot_updates(self, offset: Optional[int] = None) -> Dict[str, Any]:
        """
        Get updates (new messages) from the bot.
        
        Args:
            offset: Update ID offset
            
        Returns:
            JSON response with updates
        """
        url = f"https://api.telegram.org/bot{self.TOKEN}/getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        
        response = requests.get(url, params=params)
        return response.json()
    
    def process_updates(self, minutes: int = 1) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Process updates to detect new private messages.
        
        Args:
            minutes: Number of minutes to check for updates
            
        Returns:
            Dictionary of new users if any, None otherwise
        """
        # Start with no offset
        offset = None
        
        # Get the current time
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=minutes)
        
        print(f"Checking for new users from {start_time} to {end_time}")
        
        while datetime.now() < end_time:
            updates = self.get_bot_updates(offset)
            print(updates)
            if updates["ok"]:
                for update in updates["result"]:
                    # Update the offset to acknowledge this update
                    offset = update["update_id"] + 1
                    
                    # Check if this is a private message (not from a group)
                    if "message" in update and "chat" in update["message"]:
                        chat = update["message"]["chat"]
                        
                        # Check if this is a private chat
                        if chat["type"] == "private":
                            user_id = chat["id"]
                            user_info = {
                                "id": user_id,
                                "first_name": chat.get("first_name", "User"),
                                "username": chat.get("username", ""),
                                # Add message_id to user_info
                                "message_id": update["message"].get("message_id")
                            }
                            
                            print(f"New user detected: {user_info['first_name']}")
                            return {str(user_id): user_info}
            
            # Sleep briefly to avoid excessive API calls
            time.sleep(2)
        
        print(f"No user found in {minutes} minutes")
        return None
    
    def send_private_message(self, user_id: Union[str, int], first_name: str, contact_number: str, location:str, date:str, pick_up_time:str, user_message_id: Optional[int] = None) -> bool:
        """
        Send a private message to a user.
        
        Args:
            user_id: User's Telegram ID
            first_name: User's first name
            contact_number: Contact number to share with the user
            user_message_id: ID of the user's original message to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Delete the user's /start message if provided
        if user_message_id:
            self.delete_message(user_id, user_message_id)
            print(f"Deleted user's start message (ID: {user_message_id})")

        clean_number = contact_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        message = (
            f"Hello <b>{first_name}</b>!\n" 
            f"Thank you for signing in. You're now registered.\n" 
            f"Request for an Event Pick Up:\n\n"
            f"<b>Where:</b> <i>{location}</i> \n"
            f"<b>When:</b> <i>{date}</i> \n"
            f"<b>Time:</b> <i>{pick_up_time}</i> \n\n"
            f"Please reach out to the Event host as soon as possible to:\n"
            f"<b>1.</b> Confirm Pick up.\n"
            f"<b>2.</b> Ask for pick-up time and amount.\n"
            f"\n"
            f"Call Event Host:"
            f"<a href=\"tel:{clean_number}\">{contact_number}</a>"
            f"\n"
            f"\n"
            f"Call now, message will be deleted in 15 minutes."
        )

        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage"
        params = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.get(url, params=params)
        result = response.json()

        if result["ok"]:
            print(f"Private message sent to {first_name}")
            # Get the message ID from the response
            sent_message_id = result["result"]["message_id"]
            # Schedule message deletion after 2 seconds
            self.schedule_message_deletion(user_id, sent_message_id, 900)
            return True
        else:
            print(f"Failed to send private message to {first_name}")
            return False
        
    def delete_message(self, chat_id: Union[str, int], message_id: int) -> bool:
        """
        Delete a specific message.
        
        Args:
            chat_id: Chat ID where the message was sent
            message_id: ID of the message to delete
            
        Returns:
            True if successful, False otherwise
        """
        url = f"https://api.telegram.org/bot{self.TOKEN}/deleteMessage"
        params = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result["ok"]:
            print(f"Deleted message {message_id} in chat {chat_id}")
            return True
        else:
            print(f"Failed to delete message {message_id} in chat {chat_id}")
            return False
        
    def delete_original_message(self) -> bool:
        """
        Delete the original message from the group.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.message_id:
            print("No message ID available to delete")
            return False
        
        url = f"https://api.telegram.org/bot{self.TOKEN}/deleteMessage"
        params = {
            "chat_id": self.chat_id,
            "message_id": self.message_id
        }
        
        response = requests.get(url, params=params)
        if response.json()["ok"]:
            print(f"Original message (ID: {self.message_id}) deleted successfully")
            return True
        else:
            print(f"Failed to delete original message")
            return False
    
    def send_confirmation_to_group(self, user_info: Dict[str, Any], date, pick_up_time) -> bool:
        """
        Send a confirmation message to the group about who signed in.
        
        Args:
            user_info: Dictionary containing user information
            
        Returns:
            True if successful, False otherwise
        """
        name = user_info["first_name"]
        username = user_info.get("username", "")
        
        if username:
            message = f"<b>{name}</b> (@{username}) is signing in for Pick-Up at {date}, {pick_up_time}."
        else:
            message = f"<b>{name}</b> is signing in"
        
        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.get(url, params=params)
        if response.json()["ok"]:
            print(f"Confirmation message sent to group")
            return True
        else:
            print(f"Failed to send confirmation message to group")
            return False
    
    def send_denial_to_group(self) -> bool:
        """
        Send a denial message to the group that nobody signed in.
        
        Returns:
            True if successful, False otherwise
        """
        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": "Unfortunately, no one has time for a pick up.",
            "parse_mode": "HTML"
        }
        
        response = requests.get(url, params=params)
        if response.json()["ok"]:
            print(f"Denial message sent to group")
            return True
        else:
            print(f"Failed to send denial message to group")
            return False
    
    def run_pickup_workflow(self, location: str, date: str, pick_up_time: str, 
                        contact_number: str, wait_minutes: int = 1) -> bool:
        """
        Run the complete pickup workflow.
        
        Args:
            location: Pickup location
            date: Date of the pickup
            pick_up_time: Time of the pickup
            contact_number: Contact number for the pickup
            wait_minutes: Number of minutes to wait for responses
            
        Returns:
            True if a user picked up, False otherwise
        """
        # Reset the bot to clear any previous state
        self.reset_bot_completely()
        
        # Send the message with the button
        self.send_message_emergency_group(location=location, date=date, pick_up_time=pick_up_time)
        
        # Check for responses
        new_users = self.process_updates(minutes=wait_minutes)
        
        # Delete the original message in any case
        self.delete_original_message()
        
        # Handle user responses
        if new_users:
            for user_id, user_info in new_users.items():
                print(new_users.items())
                self.send_private_message(
                    user_id=user_id, 
                    first_name=user_info["first_name"], 
                    contact_number=contact_number,
                    user_message_id=user_info.get("message_id"),  # Pass the message ID
                    location= location,
                    date= date,
                    pick_up_time= pick_up_time
                )
                self.send_confirmation_to_group(user_info, date=date, pick_up_time=pick_up_time)
            return True
        else:
            self.send_denial_to_group()
            return False