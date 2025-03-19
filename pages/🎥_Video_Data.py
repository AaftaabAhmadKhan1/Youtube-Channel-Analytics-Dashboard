import streamlit as st
from pytube import YouTube
from googleapiclient.discovery import build

# Session state validation
if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🔑 API key required! Please return to the main page.")
    st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")
    st.stop()

if 'video_id' not in st.session_state or not st.session_state.video_id:
    st.error("❌ No video selected! Please choose a video from the main page.")
    st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")
    st.stop()

def get_video_stats(video_id, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.videos().list(part="statistics,snippet,contentDetails", id=video_id)
    response = request.execute()
    return response['items'][0] if response.get('items') else None

def main():
    st.set_page_config(page_title="Video Analytics", layout="wide")
    st.title("🎥 Detailed Video Analytics")
    
    try:
        video_data = get_video_stats(st.session_state.video_id, st.session_state.api_key)
        if not video_data:
            st.error("🚫 Video data not found")
            st.stop()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(video_data['snippet']['thumbnails']['high']['url'])
            st.link_button("Watch on YouTube", f"https://youtu.be/{st.session_state.video_id}")
        
        with col2:
            st.markdown(f"### {video_data['snippet']['title']}")
            st.markdown(f"**Channel:** {video_data['snippet']['channelTitle']}")
            st.markdown(f"**Published:** {video_data['snippet']['publishedAt'][:10]}")
            st.markdown(f"**Duration:** {video_data['contentDetails']['duration']}")
            
            cols = st.columns(4)
            metrics = [
                ('👀 Views', 'viewCount'),
                ('👍 Likes', 'likeCount'),
                ('💬 Comments', 'commentCount'),
                ('📊 Engagement', f"{(int(video_data['statistics'].get('likeCount', 0)) / int(video_data['statistics']['viewCount']):.2%}")
            ]
            
            for col, (label, key) in zip(cols, metrics):
                with col:
                    if key == 'engagement':
                        st.metric(label, video_data['statistics'].get(key, 'N/A'))
                    else:
                        value = int(video_data['statistics'].get(key, 0))
                        st.metric(label, f"{value:,}")

        st.divider()
        st.markdown("### 📝 Description")
        st.write(video_data['snippet']['description'])

    except Exception as e:
        st.error(f"❌ Error loading video data: {str(e)}")
        st.page_link("🏠_Home.py", label="🏠 Return to Main Page", icon="🏠")

if __name__ == "__main__":
    main()
