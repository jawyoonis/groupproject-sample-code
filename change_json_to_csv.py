import json
import csv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to convert JSON data to CSV format for community detection
def json_to_csv_with_labels(json_file, csv_file):
    # Read JSON data
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Prepare a list for CSV output
    csv_data = []

    # Iterate through each user in the JSON data
    for user_id, user_data in data.items():
        user_id = int(user_id)  # Convert user ID to integer
        friends_list = user_data.get('friends', [])
        friend_count = len(friends_list)  # Calculate the number of friends

        # Determine label for multiple friends
        if friend_count > 1:
            has_multiple_friends = "Multiple Friends"
        else:
            has_multiple_friends = "Single/No Friends"

        # Add entry for each friend (direct friends only)
        if friend_count > 0:  # Only add rows for users with friends
            for friend in friends_list:
                friend_id = friend['id']
                # Ensure that we are only adding direct connections between user and their friends
                csv_data.append([user_id, friend_id, friend_count, has_multiple_friends])
                logging.info(f"Added edge: UserID={user_id}, FriendID={friend_id}, FriendCount={friend_count}, Label={has_multiple_friends}")

    # Write the data to a CSV file
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(['UserID', 'FriendID', 'FriendCount', 'HasMultipleFriends'])
        # Write rows
        writer.writerows(csv_data)
    
    logging.info(f"CSV file '{csv_file}' has been created successfully.")

# Main function to drive the conversion
def main():
    json_file = 'user_and_friends_data.json'  # Input JSON file
    csv_file = 'user_and_friends_edges_with_labels.csv'  # Output CSV file
    json_to_csv_with_labels(json_file, csv_file)

# Run the script
if __name__ == "__main__":
    main()
