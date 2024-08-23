import streamlit as st

st.logo(image='media\\logo.png')
# pg = st.navigation([st.Page("audio_ui.py", title="Audio Diarization")])
pg = st.navigation([st.Page("video_ui.py", title="Video Diarization")])
pg.run()
