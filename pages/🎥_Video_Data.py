import streamlit as st
from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------
# Session State Validation
# ---------------------------
if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🔑 API key missing! Please return to the main page first.")
    st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")
    st.stop()

if 'video_id' not in st.session_state or not st.session_state.video_id:
    st.error("❌ No video selected! Please choose a video from the main page.")
    st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")
    st.stop()

# ---------------------------
# Core Functions
# ---------------------------
@st.cache_data(show_spinner="📡 Fetching video data...")
def get_video_stats(_api_key, video_id):
    try:
        youtube = build('youtube', 'v3', developerKey=_api_key)
        request = youtube.videos().list(
            part="statistics,snippet,contentDetails,status",
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            return None
            
        data = response['items'][0]
        return {
            'title': data['snippet']['title'],
            'channel': data['snippet']['channelTitle'],
            'published': data['snippet']['publishedAt'],
            'duration': data['contentDetails']['duration'],
            'views': int(data['statistics']['viewCount']),
            'likes': int(data['statistics'].get('likeCount', 0)),
            'comments': int(data['statistics'].get('commentCount', 0)),
            'thumbnail': data['snippet']['thumbnails']['high']['url'],
            'description': data['snippet']['description'],
            'privacy': data['status']['privacyStatus']
        }
        
    except HttpError as e:
        st.error(f"YouTube API Error: {e.error_details[0]['reason']}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

# ---------------------------
# Main Page Layout
# ---------------------------
def main():
    st.set_page_config(page_title="Video Analytics", layout="wide")
    st.title("🎥 Detailed Video Analytics")
    
    # Get video data
    video_data = get_video_stats(st.session_state.api_key, st.session_state.video_id)
    
    if not video_data:
        st.error("Failed to load video data")
        st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")
        st.stop()
    
    # ---------------------------
    # Video Header Section
    # ---------------------------
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.image(video_data['thumbnail'], use_column_width=True)
        st.link_button(
            "▶️ Watch on YouTube", 
            f"https://youtu.be/{st.session_state.video_id}",
            use_container_width=True
        )
    
    with col2:
        st.markdown(f"### {video_data['title']}")
        st.caption(f"**Channel:** {video_data['channel']}")
        
        cols = st.columns(4)
        with cols[0]:
            st.metric("Published", video_data['published'][:10])
        with cols[1]:
            st.metric("Duration", video_data['duration'].replace('PT', '').lower())
        with cols[2]:
            st.metric("Privacy", video_data['privacy'].capitalize())
        with cols[3]:
            engagement = (video_data['likes'] + video_data['comments']) / video_data['views'] * 100
            st.metric("Engagement Rate", f"{engagement:.2f}%")
    
    # ---------------------------
    # Key Metrics
    # ---------------------------
    st.divider()
    
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("Total Views", f"{video_data['views']:,}", 
                 help="Total views since publication")
    with metric_cols[1]:
        st.metric("Likes", f"{video_data['likes']:,}", 
                 delta=f"{(video_data['likes']/video_data['views']*100):.1f}% of views",
                 help="Like percentage relative to views")
    with metric_cols[2]:
        st.metric("Comments", f"{video_data['comments']:,}", 
                 delta=f"{(video_data['comments']/video_data['views']*100):.1f}% of views",
                 help="Comment percentage relative to views")
    
    # ---------------------------
    # Video Description
    # ---------------------------
    st.divider()
    st.subheader("Description")
    st.markdown(f"```\n{video_data['description']}\n```")
    
    # ---------------------------
    # Navigation Footer
    # ---------------------------
    st.divider()
    if st.button("← Return to Channel Analytics", use_container_width=True):
        st.switch_page("🏠_Home.py")

if __name__ == "__main__":
    main()
