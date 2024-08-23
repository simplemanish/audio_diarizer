import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text
import pandas as pd
import altair as alt
from sentiment_analysis import analyze_sentiment
from utilities.video_indexer import VideoIndexer
import upload_to_aisearch
import os
from dotenv import load_dotenv
import queryHandler

load_dotenv()

st.set_page_config(layout='wide')
state = st.session_state

index_name = os.getenv("AZURE_SEARCH_VIDEO_INDEX_NAME")

if "messages" not in state:
    state.messages = []

if "mapping" not in state:
    state.mapping = dict()

if "uploaded_files" not in state:
    state.uploaded_files = ["Choose video"]

if "audio_mapping" not in state:
    state.audio_mapping = dict()

if 'text_received' not in state:
    state.text_received = []

if 'recording' not in state:
    state.recording = False

if 'count' not in state:
    state.count = 1

# Display chat messages from history on app rerun
for message in state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
st.markdown("# Video Bot")
st.sidebar.header("Video Diarization")

# lang_options = {
#     "English (India)": "en-IN",
#     "English (US)": "en-US",
#     "English (UK)": "en-GB",
#     "Japanese": "ja-JP"
# }
# selected_lang = st.sidebar.selectbox(
#     "Select the language of the video", list(lang_options))

# cols_1 = st.columns(2)

# audio = st.sidebar.file_uploader("Upload a video file", type=[
#                                  "mp4", "mpeg4"], on_change=None)

# if audio is not None and audio.name not in state.uploaded_files:
#     file_name = audio.name
#     state.uploaded_files.add(file_name)
#     state.audio_mapping[file_name] = audio
vi = VideoIndexer()
video_list = vi.get_video_list()
# count = 1 
if state.count == 1:
    for i in video_list:
        state.uploaded_files.append(i["video_name"])
    state.count += 1
file_selected = st.sidebar.selectbox(
    "Which Audio File you want to process?", state.uploaded_files)
if file_selected:
    for item in video_list:
        if item["video_name"] == file_selected:
            video_id = item["video_id"]
            if item["video_state"] == "Processed":
                st.sidebar.success(f'{item["video_name"]} is Proccesed')
            else:
                st.sidebar.error(f'{item["video_name"]} is still processing')

# phrase_info = "Enter a phrase related to the audio or your analysis."
# phrase_input = st.sidebar.text_input(
#     "Phrase",
#     placeholder="Enter phrase",
#     help=phrase_info
# )

is_audio = st.sidebar.checkbox(
    'Perform Audio Analysis', key='is_audio', on_change=None)
# perform_sentiment_analysis = st.sidebar.checkbox(
#     'Perform Sentiment Analysis', key='perform_sentiment_analysis', on_change=None)

# if perform_sentiment_analysis:
#     st.markdown("Sentiment Analysis")

#     if file_selected:
#         audio_file = state.audio_mapping.get(file_selected)
#         if audio_file:
#             progress_bar = st.sidebar.empty()
#             progres_text = st.sidebar.empty()

#             progress_bar.progress(0)
#             progres_text.text("Processing.....")

#             transcription, sentiment_scores = analyze_sentiment(audio_file)

#             print('Transcribed text: ', transcription)

#             progress_bar.progress(100)
#             progres_text.text("Processing Complete.....")

#             sentiment_labels = ["Positive", "Neutral", "Negative"]
#             sentiment_values = [
#                 sentiment_scores['pos'],
#                 sentiment_scores['neu'],
#                 sentiment_scores['neg']
#             ]

#             sentiment_data = pd.DataFrame({
#                 "Sentiment": sentiment_labels,
#                 "Score": sentiment_values
#             })

#             sentiment_data["Color"] = sentiment_data["Score"].apply(
#                 lambda x: "#4CAF50" if x > 0.5 else "#FFC107" if x > 0 else "#F44336"
#             )

#             chart = alt.Chart(sentiment_data).mark_bar().encode(
#                 x="Sentiment:O",
#                 y="Score:Q",
#                 color=alt.Color("Color:N", scale=None),
#                 tooltip=["Sentiment:N", "Score:Q"]
#             ).properties(
#                 title="Sentiment Analysis Scores"
#             )

#             st.altair_chart(chart, use_container_width=True)
#         else:
#             st.error("Error: No audio file found")


if is_audio:
    st.markdown("Video Diarization")
    if file_selected == "Choose video":
        st.sidebar.error("Please select the file")
    else:
        print("file_selected :",file_selected)
        for item in video_list:
            if item["video_name"] == file_selected:
                video_id = item["video_id"]
                # if item["video_state"] == "Processed":
                #     st.sidebar.success(f'{item["video_name"]} is Proccesed')
                print("video_id :",video_id)
                diarize = vi.get_indexed_video_data(video_id=video_id)
                
                upload_to_aisearch.get_text_chunks(diarize,file_selected,index_name)
                st.text(diarize)

else:
    if state.uploaded_files:
        if prompt := st.chat_input("What is up?"):
            queryHandler.handle_userinput(prompt,index_name)
            for i, message in enumerate(st.session_state.chat_history):
                if i % 2 == 0:
                    with st.chat_message("user"):
                        st.write(message)
                else:
                    with st.chat_message("assistant"):
                        st.write(message)
        #     state.messages.append({"role": "user", "content": prompt})
        # # Display user message in chat message container
        #     with st.chat_message("user"):
        #         st.markdown(prompt)

        #     with st.chat_message("assistant"):
        #         if is_audio and file_selected:
        #             response = st.write_stream(get_response(
        #                 file_selected, prompt, state.mapping, True))
        #             state.messages.append(
        #                 {"role": "assistant", "content": response})
        #         else:
        #             response = st.write_stream(get_response(
        #                 file_selected, prompt, state.mapping, False))
        #             state.messages.append(
        #                 {"role": "assistant", "content": response})

                # st.download_button('Download Text', response)
    else:
        st.chat_input(disabled=True)

    cols_2 = st.columns(16)
    with cols_2[15]:
        for i in range(22):
            st.write("")
        if st.button("🎙️" if not state.recording else "🛑"):
            if state.recording:
                state.recording = False
                audio_data = mic_recorder()
                transcribed_text = speech_to_text(audio_data)
                st.chat_input(transcribed_text)
            else:
                state = True
                mic_recorder()
