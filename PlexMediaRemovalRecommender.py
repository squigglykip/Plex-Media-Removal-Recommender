import os
import time
import threading
import requests
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from plexapi.server import PlexServer
from sklearn.preprocessing import MinMaxScaler
from dotenv import load_dotenv
from config import PLAY_COUNT_WEIGHT, RATING_WEIGHT, AGE_WEIGHT, SIZE_WEIGHT

# Load environment variables from .env file
load_dotenv()

# Constants
PLEX_SERVERS = [
    {
        'name': os.getenv('PLEX_SERVER_NAME'),
        'baseurl': os.getenv('PLEX_SERVER_BASEURL'),
        'token': os.getenv('PLEX_SERVER_TOKEN')
    }
]
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def get_media_data(server_info):
    plex = PlexServer(server_info['baseurl'], server_info['token'])
    media_data = []
    
    for section in plex.library.sections():
        if section.type == 'show':
            for show in section.all():
                for episode in show.episodes():
                    total_size = sum(part.size for part in episode.media[0].parts) if episode.media and episode.media[0].parts else 0
                    play_count = episode.viewCount or 0

                    media_data.append({
                        'Title': f"{show.title} - {episode.title}",
                        'Play Count': play_count,
                        'File Size': total_size,
                        'Rating': episode.rating or 0,
                        'Audience Rating': episode.audienceRating or 0,
                        'Added At': episode.addedAt,
                        'Source': 'TV Show'
                    })
                
        elif section.type == 'movie':
            for movie in section.all():
                total_play_count = movie.viewCount or 0
                total_size = sum(part.size for part in movie.iterParts() if part.size is not None)
                
                media_data.append({
                    'Title': movie.title,
                    'Play Count': total_play_count,
                    'File Size': total_size,
                    'Rating': movie.rating or 0,
                    'Audience Rating': movie.audienceRating or 0,
                    'Added At': movie.addedAt,
                    'Source': 'Movie'
                })
    
    return media_data

def filter_by_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    return df[df[column] <= Q1]

def calculate_removal_score(df):
    required_columns = ['Play Count', 'Effective Rating', 'Age in Days', 'File Size']
    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"DataFrame must contain the following columns: {', '.join(required_columns)}")

    def iqr_rank(column):
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        if IQR == 0:
            return df[column].apply(lambda x: 0 if x == 0 else 1)
        return (df[column] - Q1) / IQR

    df = df.copy()
    df.loc[:, 'IQR Play Count'] = iqr_rank('Play Count')
    df.loc[:, 'IQR Rating'] = iqr_rank('Effective Rating')
    df.loc[:, 'IQR Age'] = iqr_rank('Age in Days')
    df.loc[:, 'IQR File Size'] = iqr_rank('File Size')

    scaler = MinMaxScaler()
    df.loc[:, 'Normalized Play Count'] = 1 - scaler.fit_transform(df[['IQR Play Count']])
    df.loc[:, 'Normalized Effective Rating'] = 1 - scaler.fit_transform(df[['IQR Rating']])
    df.loc[:, 'Normalized Age in Days'] = scaler.fit_transform(df[['IQR Age']])
    df.loc[:, 'Normalized File Size'] = scaler.fit_transform(df[['IQR File Size']])

    df.loc[:, 'Removal Score'] = (
        PLAY_COUNT_WEIGHT * df['Normalized Play Count'] +
        RATING_WEIGHT * df['Normalized Effective Rating'] +
        AGE_WEIGHT * df['Normalized Age in Days'] +
        SIZE_WEIGHT * df['Normalized File Size']
    )

    df.loc[:, 'Removal Recommendation'] = pd.cut(
        df['Removal Score'], 
        bins=[0, 0.33, 0.66, 1], 
        labels=['Low', 'Medium', 'High']
    )

    df_sorted = df.sort_values(by='Removal Score', ascending=False)
    return df_sorted[['Show Title', 'Play Count', 'Effective Rating', 'Age in Days', 'File Size', 'Removal Score', 'Removal Recommendation']]

def format_table_for_discord(df, title):
    df = df.drop(columns=['Removal Score'])
    table_str = tabulate(df, headers='keys', tablefmt='simple', showindex=False)
    return f"**{title}**\n```\n{table_str}\n```"

def send_discord_message(content):
    data = {"content": content}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Message successfully sent to Discord.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")

def animate_processing():
    def animate():
        while not done:
            for dot_count in range(1, 4):
                print(f"Processing{'.' * dot_count}", end="\r", flush=True)
                time.sleep(0.5)
            print(" " * 15, end="\r", flush=True)

    global done
    done = False
    animation_thread = threading.Thread(target=animate)
    animation_thread.start()

    return animation_thread

def main():
    # Start the animation
    animation_thread = animate_processing()

    media_data = []
    for server in PLEX_SERVERS:
        media_data.extend(get_media_data(server))

    media_df = pd.DataFrame(media_data)
    media_df['Effective Rating'] = media_df.apply(
        lambda row: row['Rating'] if row['Rating'] != 0 else row['Audience Rating'],
        axis=1
    )
    media_df['Show Title'] = media_df['Title'].str.split(' - ').str[0]

    grouped_df = media_df.groupby(['Show Title', 'Source'], as_index=False).agg({
        'Effective Rating': 'first',
        'Audience Rating': 'mean',
        'Added At': 'min',
        'Play Count': 'sum',
        'File Size': 'sum'
    })
    grouped_df['Age in Days'] = (datetime.now() - pd.to_datetime(grouped_df['Added At'])).dt.days

    movies_df = grouped_df[grouped_df['Source'] == 'Movie']
    tv_shows_df = grouped_df[grouped_df['Source'] == 'TV Show']

    movies_to_remove = filter_by_iqr(movies_df, 'Play Count').index.intersection(
        filter_by_iqr(movies_df, 'Effective Rating').index).intersection(
        filter_by_iqr(movies_df, 'Age in Days').index)

    tv_shows_to_remove = filter_by_iqr(tv_shows_df, 'Play Count').index.intersection(
        filter_by_iqr(tv_shows_df, 'Effective Rating').index).intersection(
        filter_by_iqr(tv_shows_df, 'Age in Days').index)

    movies_final = calculate_removal_score(movies_df.loc[movies_to_remove])
    tv_shows_final = calculate_removal_score(tv_shows_df.loc[tv_shows_to_remove])

    movies_table = format_table_for_discord(movies_final, "🎬 Movies to Recommend for Removal")
    tv_shows_table = format_table_for_discord(tv_shows_final, "📺 TV Shows to Recommend for Removal")

    send_discord_message(movies_table)
    send_discord_message(tv_shows_table)

    # Stop the animation
    global done
    done = True
    animation_thread.join()
    print("Processing... Done!")

if __name__ == "__main__":
    main()
