# Plex Media Removal Recommender

This script helps you identify and recommend media files (movies and TV shows) for removal from your Plex server based on various criteria such as play count, rating, age, and file size. The recommendations are sent to a specified Discord channel via a webhook.

## How It Works

1. **Data Retrieval**: The script connects to your Plex server using the details provided in the `.env` file and retrieves media data (movies and TV shows) from your Plex library.
2. **Data Aggregation**: It aggregates the media data, calculating the total play count, file size, and effective rating for each media file. The effective rating is determined by using the rating if available, otherwise, it uses the audience rating.
3. **Age Calculation**: The script calculates the age of each media file in days from the date it was added to the library.
4. **Filtering by IQR**: It filters the media files using the Interquartile Range (IQR) method to identify the lower quartile of media files based on play count, effective rating, and age.
5. **Normalization**: The script normalizes the filtered data using MinMaxScaler to scale the values between 0 and 1. The play count and effective rating are inverted (1 - normalized value) to prioritize lower values.
6. **Weighting and Scoring**: It calculates a removal score for each media file using a weighted sum of the normalized play count, effective rating, age, and file size. The default weights are 0.3 for play count, 0.3 for rating, 0.2 for age, and 0.2 for file size.
7. **Recommendation**: Based on the removal score, the script categorizes the media files into three recommendation levels: Low, Medium, and High. These recommendations are then formatted into a table.
8. **Notification**: Finally, the script sends the formatted recommendations to the specified Discord channel via a webhook.

## Requirements

- Python 3.x
- A Plex server
- A Discord account with a webhook URL

## Setup

1. Clone this repository to your local machine.
2. Install the required Python packages using pip:
    ```sh
    pip install -r requirements.txt
    ```
3. Create a `.env` file in the root directory of the project with the following details:

    ```env
    # The name of your Plex server. This is used for identification purposes.
    PLEX_SERVER_NAME=Your Plex Server Name

    # The base URL of your Plex server. This should include the protocol (http/https) and the port number.
    # Example: http://your-plex-server-ip:32400
    PLEX_SERVER_BASEURL=http://your-plex-server-ip:32400

    # The authentication token for accessing your Plex server. This token is required to interact with the Plex API.
    # You can obtain this token from your Plex account settings.
    PLEX_SERVER_TOKEN=Your Plex Token

    # The Discord webhook URL where the removal recommendations will be sent.
    # You can create a webhook in your Discord server settings and paste the URL here.
    DISCORD_WEBHOOK_URL=Your Discord Webhook URL
    ```

## Usage

1. Run the script:
    ```sh
    python PlexMediaRemovalRecommender.py
    ```
2. The script will start processing your media files and send the removal recommendations to the specified Discord channel.

## How It Works

1. The script connects to your Plex server using the details provided in the `.env` file.
2. It retrieves media data (movies and TV shows) from your Plex library.
3. It calculates a removal score for each media file based on play count, rating, age, and file size.
4. It formats the recommendations and sends them to the specified Discord channel via a webhook.

## Functions

- `get_media_data(server_info)`: Retrieves media data from the Plex server.
- `filter_by_iqr(df, column)`: Filters data based on the Interquartile Range (IQR).
- `calculate_removal_score(df, play_count_weight=0.3, rating_weight=0.3, age_weight=0.2, size_weight=0.2)`: Calculates the removal score for media files.
- `format_table_for_discord(df, title)`: Formats the data into a table for Discord.
- `send_discord_message(content)`: Sends a message to the specified Discord channel.
- `animate_processing()`: Displays a processing animation in the console.
- `main()`: Main function that orchestrates the entire process.

## Example

Here is an example of the output sent to Discord:

![alt text](image.png)
