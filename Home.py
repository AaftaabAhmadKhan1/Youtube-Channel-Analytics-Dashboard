import datetime
import streamlit as st
import io
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd

from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.chart_container import chart_container
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo

from prophet import Prophet

from channelDataExtraction import getChannelData
from channelVideoDataExtraction import *

########################################################################################################################
#                                               FUNCTIONS
########################################################################################################################
@st.cache_data
def download_data(api_key, channel_id):
    channel_details = getChannelData(api_key, channel_id)

    if channel_details is None:
        return None, None, None, None

    videos = getVideoList(api_key, channel_details["uploads"])
    videos_df = pd.DataFrame(videos)
    video_ids = [video['id'] for video in videos if video['id'] is not None]
    all_video_data = buildVideoListDataframe(api_key, video_ids)

    st.session_state.start_index = 0
    st.session_state.end_index = 10
    st.session_state['video_id'] = None
    st.session_state.all_video_df = all_video_data
    st.session_state.api_key = api_key

    return channel_details, videos, all_video_data, videos_df


def display_video_list(video_data, start_index, end_index, search_query=None):
    if search_query is None:
        search_query = ""
    new_search_query = st.text_input("Search Videos by Title", search_query)

    if 'start_index' not in st.session_state:
        st.session_state.start_index = start_index
    if 'end_index' not in st.session_state:
        st.session_state.end_index = end_index

    if new_search_query != search_query:
        st.session_state.start_index = start_index
        st.session_state.end_index = end_index

    filtered_videos = [video for video in video_data if new_search_query.lower() in video['title'].lower()]
    paginated_videos = filtered_videos[st.session_state.start_index:st.session_state.end_index]

    for video in paginated_videos:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.image(video['thumbnail'])
        with col2:
            st.write(video['id'])
        with col3:
            st.write(video['title'])
        with col4:
            video_stats = st.button("Check Video Statistics", key=video['id'])
            if video_stats:
                st.session_state['video_id'] = video['id']
                switch_page("video_data")

    if st.session_state.end_index < len(filtered_videos):
        if st.button('Load next 10 videos', key='load_next'):
            st.session_state.start_index = st.session_state.end_index
            st.session_state.end_index += 10

########################################################################################################################
#                                       MAIN PAGE CONFIGURATION
########################################################################################################################
st.set_page_config(page_title="Physics Wallah Youtube Channel Analytics Dashboard", page_icon="📊", layout="wide")

st.title("Physics Wallah YouTube Analytics Dashboard")
st.sidebar.title("Settings")

if 'API_KEY' not in st.session_state:
    st.session_state.API_KEY = "YOUR_YOUTUBE_API_KEY"
if 'CHANNEL_ID' not in st.session_state:
    st.session_state.CHANNEL_ID = ""

st.session_state.CHANNEL_ID = st.sidebar.text_input("Enter the YouTube Channel ID", st.session_state.CHANNEL_ID)

if not st.session_state.API_KEY or not st.session_state.CHANNEL_ID:
    st.warning("Please enter your Channel ID.")
    st.stop()

refresh_button = st.sidebar.button("Refresh Data")
channel_details, videos, all_video_data, videos_df = download_data(st.session_state.API_KEY, st.session_state.CHANNEL_ID)

if channel_details is None:
    st.warning("Invalid YouTube Channel ID. Please check and enter a valid Channel ID.")
    st.stop()

if refresh_button:
    with st.spinner("Refreshing data..."):
        channel_details, videos, all_video_data, videos_df = download_data(st.session_state.API_KEY, st.session_state.CHANNEL_ID)
        if channel_details is None:
            st.warning("Invalid YouTube Channel ID. Please check and enter a valid Channel ID.")
            st.stop()

st.sidebar.title("Data Filters")
num_videos = st.sidebar.slider("Select Number of Top Videos to Display:", 1, 50, 10)

all_video_data['published_date'] = pd.to_datetime(all_video_data['published_date'])
min_date = all_video_data['published_date'].min().date()
max_date = all_video_data['published_date'].max().date()

start_date = st.sidebar.date_input("Select Start Date", min_date)
end_date = st.sidebar.date_input("Select End Date", max_date)

if start_date > end_date:
    st.sidebar.warning("Start date should be earlier than end date.")
    st.stop()

tag_search = st.sidebar.text_input("Search Videos by Tag")

date_range_start = pd.Timestamp(start_date)
date_range_end = pd.Timestamp(end_date)

filtered_data = all_video_data[(all_video_data['published_date'] >= date_range_start) &
                               (all_video_data['published_date'] <= date_range_end)]

if tag_search:
    filtered_data = filtered_data[filtered_data['tags'].apply(lambda x: tag_search in x)]

st.header("Channel Details")
col1, col2 = st.columns([1, 2])

with col1:
    add_logo(channel_details['thumbnail'], height=300)

with col2:
    st.markdown(f"**Channel Title:** {channel_details['title']}")
    st.markdown(f"**Channel Description:** {channel_details['description']}")
    st.link_button("Go to Channel", f"https://www.youtube.com/channel/{st.session_state.CHANNEL_ID}")

col1, col2, col3 = st.columns(3)
col1.metric("Total Views", f"{int(channel_details['viewCount']):,}")
col2.metric("Subscribers", f"{int(channel_details['subscriberCount']):,}")
col3.metric("Total Videos", len(videos))
style_metric_cards(background_color="#000000", border_left_color="#049204", border_color="#0E0E0E")

st.subheader("Detailed Video Statistics Video Selection")
display_video_list(videos, 0, 10)
