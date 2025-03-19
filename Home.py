import datetime
import streamlit as st
import io
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
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
    st.session_state.video_id = None
    st.session_state.all_video_df = all_video_data

    return channel_details, videos, all_video_data, videos_df

def display_video_list(video_data, start_index, end_index, search_query=None):
    """Displays a list of videos with session state validation"""
    new_search_query = st.text_input("Search Videos by Title", search_query or "")
    
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
            if st.button("Check Video Statistics", key=video['id']):
                if 'api_key' in st.session_state and st.session_state.api_key:
                    st.session_state.video_id = video['id']
                    switch_page("pages/🎥_Video_Data.py")
                else:
                    st.error("Please enter API key first")

    if st.session_state.end_index < len(filtered_videos):
        if st.button('Load next 10 videos', key='load_next'):
            st.session_state.start_index = st.session_state.end_index
            st.session_state.end_index += 10

########################################################################################################################
#                                       MAIN PAGE CONFIGURATION
########################################################################################################################
st.set_page_config(
    page_title="Physics Wallah Youtube Channel Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'channel_id' not in st.session_state:
    st.session_state.channel_id = ""

########################################################################################################################
#                                       SIDE BAR CONFIGURATION
########################################################################################################################
st.title("Physics Wallah YouTube Analytics Dashboard")

# Sidebar configuration
with st.sidebar:
    st.title("Settings")
    st.markdown("---")
    
    # API Key Input
    api_key = st.text_input(
        "🔑 YouTube API Key:",
        value=st.session_state.api_key,
        type="password",
        help="Get from Google Cloud Console"
    )
    if api_key:
        st.session_state.api_key = api_key
    
    # Channel ID Input
    channel_id = st.text_input(
        "📺 Channel ID:",
        value=st.session_state.channel_id,
        help="Find in channel URL"
    )
    if channel_id:
        st.session_state.channel_id = channel_id
    
    # Validation
    if not st.session_state.api_key or not st.session_state.channel_id:
        st.error("❌ Both fields are required")
        st.stop()
    
    # Data Refresh
    st.markdown("---")
    refresh_button = st.button("🔄 Refresh Data")
    st.markdown("---")

# Data download with error handling
try:
    with st.spinner("📡 Connecting to YouTube API..."):
        channel_details, videos, all_video_data, videos_df = download_data(
            st.session_state.api_key,
            st.session_state.channel_id
        )
except Exception as e:
    st.error(f"❌ Error fetching data: {str(e)}")
    st.stop()

if channel_details is None:
    st.error("❌ Invalid Channel ID or API Key")
    st.stop()

# Convert the 'published_date' column to datetime format
all_video_data['published_date'] = pd.to_datetime(all_video_data['published_date'])

# Data Filters
with st.sidebar:
    st.title("Data Filters")
    num_videos = st.slider("Select Number of Top Videos to Display:", 1, 50, 10)
    min_date = all_video_data['published_date'].min().date()
    max_date = all_video_data['published_date'].max().date()
    start_date = st.date_input("Select Start Date", min_date)
    end_date = st.date_input("Select End Date", max_date)
    tag_search = st.text_input("Search Videos by Tag")

if start_date > end_date:
    st.sidebar.warning("Start date should be earlier than end date.")
    st.stop()

date_range_start = pd.Timestamp(start_date)
date_range_end = pd.Timestamp(end_date)

filtered_data = all_video_data[(all_video_data['published_date'] >= date_range_start) &
                               (all_video_data['published_date'] <= date_range_end)]

if tag_search:
    filtered_data = filtered_data[filtered_data['tags'].apply(lambda x: tag_search in x)]

########################################################################################################################
#                                       CHANNEL DETAILS AREA
########################################################################################################################
st.header("Channel Details", divider="green")
col1, col2, col3 = st.columns(3)

with col1:
    add_logo(channel_details['thumbnail'], height=300)
    view_count = int(channel_details['viewCount'])
    subscriber_count = int(channel_details['subscriberCount'])
    st.markdown(f"**Channel Title:** {channel_details['title']}")
    st.markdown(f"**Channel Description:** {channel_details['description']}")

with col3:
    st.link_button("Go to Channel", f"https://www.youtube.com/channel/{st.session_state.channel_id}")

col1, col2, col3 = st.columns(3)
col1.metric("Total Views", f"{view_count:,}", "")
col2.metric("Subscribers", f"{subscriber_count:,}", "")
col3.metric("Total Videos", len(videos), "")
style_metric_cards(background_color="#000000", border_left_color="#049204", border_color="#0E0E0E")

########################################################################################################################
#                                            TOP VIDEO GRAPHS
########################################################################################################################
col1, col2, col3 = st.columns(3)

# Top Views
with col1:
    st.subheader(f"Top {num_videos} Videos by Views")
    top_views_df = filtered_data.sort_values(by='view_count', ascending=False).head(num_videos)
    with chart_container(top_views_df):
        fig = px.bar(top_views_df, x='title', y='view_count')
        fig.update_layout(xaxis_title="Video Title", yaxis_title="View Count")
        fig.update_traces(marker_color='green')
        st.plotly_chart(fig, use_container_width=True)

# Top Likes
with col2:
    st.subheader(f"Top {num_videos} Videos by Likes")
    top_likes_df = filtered_data.sort_values(by='like_count', ascending=False).head(num_videos)
    with chart_container(top_likes_df):
        fig = px.bar(top_likes_df, x='title', y='like_count')
        fig.update_layout(xaxis_title="Video Title", yaxis_title="Like Count")
        fig.update_traces(marker_color='orange')
        st.plotly_chart(fig, use_container_width=True)

# Top Comments
with col3:
    st.subheader(f"Top {num_videos} Videos by Comments")
    top_comments_df = filtered_data.sort_values(by='comment_count', ascending=False).head(num_videos)
    with chart_container(top_comments_df):
        fig = px.bar(top_comments_df, x='title', y='comment_count')
        fig.update_layout(xaxis_title="Video Title", yaxis_title="Comment Count")
        fig.update_traces(marker_color='green')
        st.plotly_chart(fig, use_container_width=True)

########################################################################################################################
#                                            GROWTH ANALYTICS
########################################################################################################################
st.subheader("Viewership Growth Over Time", divider="green")
fig = go.Figure()
fig.add_trace(go.Scatter(x=filtered_data['published_date'], y=filtered_data['view_count'], 
                        mode='lines+markers', name='Views', line=dict(color='orange')))
fig.update_layout(title='Views Over Time', xaxis_title='Date', yaxis_title='Views', template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Viewership Forecast", divider="green")
with st.spinner("🔮 Predicting future views..."):
    forecast_df = filtered_data[['published_date', 'view_count']].rename(columns={'published_date': 'ds', 'view_count': 'y'})
    model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=True)
    model.fit(forecast_df)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['y'], name='Actual', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecast', line=dict(color='green')))
    fig.update_layout(title="30-Day Viewership Forecast", xaxis_title='Date', yaxis_title='Views')
    st.plotly_chart(fig, use_container_width=True)

########################################################################################################################
#                                         WORD CLOUD & RATIO ANALYSIS
########################################################################################################################
col1, col2 = st.columns(2)

# Word Cloud
with col1:
    st.subheader("Most Common Tags")
    all_tags = " ".join(" ".join(tags) for tags in filtered_data['tags'])
    wordcloud = WordCloud(width=800, height=400, background_color='black').generate(all_tags)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    st.image(buf, use_column_width=True)

# Like/View Ratio
with col2:
    st.subheader("Engagement Ratio Analysis")
    filtered_data['engagement_ratio'] = (filtered_data['like_count'] + filtered_data['comment_count']) / filtered_data['view_count']
    fig = px.scatter(filtered_data, x='published_date', y='engagement_ratio', 
                    trendline="lowess", color='view_count')
    fig.update_layout(xaxis_title='Date', yaxis_title='Engagement Ratio')
    st.plotly_chart(fig, use_container_width=True)

########################################################################################################################
#                                         VIDEO SELECTION SECTION
########################################################################################################################
st.divider()
st.subheader("Video Selection for Detailed Analysis")
display_video_list(videos, 0, 10)

# Final session state check
if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("⚠️ Session expired! Please reload and re-enter credentials.")
    st.stop()
