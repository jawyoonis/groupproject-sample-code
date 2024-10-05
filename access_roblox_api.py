import requests
import time
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt

class RobloxAPIHandler:
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Centralized function to handle API requests with retries and exponential backoff
    @retry(wait=wait_exponential(multiplier=2, min=5, max=120), stop=stop_after_attempt(10))
    def make_api_request(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logging.warning(f"Rate limit hit. Retrying...")
            raise Exception("Rate limit hit")  # Trigger retry with tenacity
        else:
            logging.error(f"Failed request with status code {response.status_code} for URL: {url}")
            return None

    # Function to retrieve user information from Roblox API
    def get_user_info(self, user_id):
        url = f"https://users.roblox.com/v1/users/{user_id}"
        return self.make_api_request(url)

    # Function to retrieve friends list for a user from Roblox API
    def get_user_friends(self, user_id):
        url = f"https://friends.roblox.com/v1/users/{user_id}/friends"
        response = self.make_api_request(url)
        return response.get('data', []) if response else []

    # Function to find a user with at least 10 friends with an iteration limit
    def find_user_with_min_friends(self, start_id, min_friends=5, max_iterations=100):
        user_id = start_id
        iterations = 0  # Initialize iteration counter
        while iterations < max_iterations:  # Stop if max_iterations is reached
            user_info = self.get_user_info(user_id)
            if user_info and not user_info.get("isBanned", False):  # Check if user exists and is not banned
                friends_list = self.get_user_friends(user_id)
                if len(friends_list) >= min_friends:  # Check if the user has at least 'min_friends' friends
                    logging.info(f"User {user_id} has {len(friends_list)} friends. Proceeding with data collection.")
                    return user_id
                else:
                    logging.info(f"User {user_id} has {len(friends_list)} friends. Trying next user...")
            else:
                logging.info(f"User ID {user_id} does not exist or is banned. Skipping...")
            
            user_id += 1  # Increment user ID and try the next one
            iterations += 1  # Increment iteration counter
            time.sleep(2)  # Fixed delay between each user ID check to avoid rate limits

        logging.error(f"Reached maximum iterations ({max_iterations}) without finding a suitable user.")
        return None  # Return None if no suitable user is found within the limit

    # Improved function to collect user data and their friends iteratively with an iteration limit
    def collect_user_and_friends_data(self, start_user_id, max_iterations=100):
        data = {}
        visited_users = set()
        queue = [start_user_id]  # Use a queue for iterative processing
        iterations = 0  # Initialize iteration counter

        while queue and iterations < max_iterations:  # Stop if max_iterations is reached
            user_id = queue.pop(0)  # Process the next user in the queue
            if user_id in visited_users:
                continue

            visited_users.add(user_id)

            # Get user info
            user_info = self.get_user_info(user_id)
            if user_info:
                logging.info(f"Retrieved data for user ID {user_id}")
                data[user_id] = {
                    "user_info": user_info,
                    "friends": []
                }

                # Get friends of the user
                friends_list = self.get_user_friends(user_id)
                if friends_list:
                    data[user_id]["friends"] = friends_list
                    for friend in friends_list:
                        friend_id = friend['id']
                        if friend_id not in visited_users:
                            queue.append(friend_id)  # Add friends to the queue for processing

            iterations += 2  # Increment iteration counter
            time.sleep(1.5)  # Global rate limiter to avoid hitting the API rate limit

        if iterations >= max_iterations:
            logging.error(f"Reached maximum iterations ({max_iterations}) during data collection.")

        return data

    # Function to save data to a JSON file
    def save_data_to_json(self, data, filename):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Data saved to {filename}")

    # Main function to drive the script
    def main(self, start_user_id, output_file):
        user_id_with_friends = self.find_user_with_min_friends(start_user_id, min_friends=5, max_iterations=100)
        if user_id_with_friends:
            data = self.collect_user_and_friends_data(user_id_with_friends, max_iterations=100)
            self.save_data_to_json(data, output_file)
        else:
            logging.error("Could not find a user with the required number of friends within the provided iteration limit.")


# Run the script
if __name__ == "__main__":
    handler = RobloxAPIHandler()
    start_user_id = 1000  # Start from a more likely valid user ID (adjust as needed)
    output_file = 'user_and_friends_data.json'
    handler.main(start_user_id, output_file)
