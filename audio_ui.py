import os
import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text
import pandas as pd
import altair as alt
from sentiment_analysis import analyze_sentiment
from conversation_diarization import ConversationDiarization
from tempfile import NamedTemporaryFile


st.set_page_config(layout='wide')
state = st.session_state

if "messages" not in state:
    state.messages = []

if "mapping" not in state:
    state.mapping = dict()

if "uploaded_files" not in state:
    state.uploaded_files = set()

if "audio_mapping" not in state:
    state.audio_mapping = dict()

if 'text_received' not in state:
    state.text_received = []

if 'recording' not in state:
    state.recording = False

if "temp_file_location" not in state:
    state.temp_file_location = dict()


# Display chat messages from history on app rerun
for message in state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
st.markdown("# Audio Bot")
st.sidebar.header("Audio Diarization")

lang_options = {
    "English (India)": "en-IN",
    "English (US)": "en-US",
    "English (UK)": "en-GB",
    "Japanese": "ja-JP"
}
selected_lang = st.sidebar.selectbox(
    "Select the language of the audio", list(lang_options))

cols_1 = st.columns(2)

audio = st.sidebar.file_uploader("Upload an audio file", type=[
                                 "mp3", "wav"], on_change=None)

if audio is not None and audio.name not in state.uploaded_files:
    file_name = audio.name
    state.uploaded_files.add(file_name)
    state.audio_mapping[file_name] = audio

file_selected = st.sidebar.selectbox(
    "Which Audio File you want to process?", state.uploaded_files)
if file_selected:
    st.sidebar.write(f"Selected File: {file_selected}")
    audio_file = state.audio_mapping.get(file_selected)
    if audio_file:
        try:
            st.sidebar.audio(audio_file.getvalue(), format="audio/wav")
        except Exception as e:
            st.sidebar.error(f"Error playing audio: {e}")

phrase_info = "Enter a phrase related to the audio or your analysis."
phrase_input = st.sidebar.text_input(
    "Phrase",
    placeholder="Enter phrase",
    help=phrase_info
)

perform_audio_diarization = st.sidebar.checkbox(
    'Perform Audio Diarization', key='perform_audio_diarization', on_change=None)
perform_sentiment_analysis = st.sidebar.checkbox(
    'Perform Sentiment Analysis', key='perform_sentiment_analysis', on_change=None)

if perform_sentiment_analysis:
    st.markdown("Sentiment Analysis")

    if file_selected:
        audio_file = state.audio_mapping.get(file_selected)
        if audio_file:
            progress_bar = st.sidebar.empty()
            progres_text = st.sidebar.empty()

            progress_bar.progress(0)
            progres_text.text("Processing.....")

            transcription, sentiment_scores = analyze_sentiment(audio_file)

            print('Transcribed text: ', transcription)

            progress_bar.progress(100)
            progres_text.text("Processing Complete.....")

            sentiment_labels = ["Positive", "Neutral", "Negative"]
            sentiment_values = [
                sentiment_scores['pos'],
                sentiment_scores['neu'],
                sentiment_scores['neg']
            ]

            sentiment_data = pd.DataFrame({
                "Sentiment": sentiment_labels,
                "Score": sentiment_values
            })

            sentiment_data["Color"] = sentiment_data["Score"].apply(
                lambda x: "#4CAF50" if x > 0.5 else "#FFC107" if x > 0 else "#F44336"
            )

            chart = alt.Chart(sentiment_data).mark_bar().encode(
                x="Sentiment:O",
                y="Score:Q",
                color=alt.Color("Color:N", scale=None),
                tooltip=["Sentiment:N", "Score:Q"]
            ).properties(
                title="Sentiment Analysis Scores"
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.error("Error: No audio file found")

elif perform_audio_diarization:
    st.markdown("Audio Diarization")
    if file_selected:
        audio_file = state.audio_mapping.get(file_selected)
        if audio_file:

            with NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                temp.write(audio_file.getvalue())
                temp.seek(0)
                temp.flush()
                state.temp_file_location[audio.name] = temp.name

                progress_bar = st.sidebar.empty()
                progres_text = st.sidebar.empty()
                progress_bar.progress(0)
                progres_text.text("Processing.....")

                # TODO: phrase list
                diarize = ConversationDiarization(
                    audio_file=state.temp_file_location.get(audio_file.name), language=lang_options[selected_lang])
                text = diarize.recognize_from_file()
                st.text(text)
                print('Diarize text: ', text)
                progress_bar.progress(100)
                progres_text.text("Processing Complete.....")
                # delete temp file
                temp.close()
                os.unlink(temp.name)
        else:
            st.error("Error: No audio file found")

else:
    if state.uploaded_files:
        if prompt := st.chat_input("What is up?"):
            state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if is_audio and file_selected:
                    response = st.write_stream(get_response(
                        file_selected, prompt, state.mapping, True))
                    state.messages.append(
                        {"role": "assistant", "content": response})
                else:
                    response = st.write_stream(get_response(
                        file_selected, prompt, state.mapping, False))
                    state.messages.append(
                        {"role": "assistant", "content": response})

                st.download_button('Download Text', response)
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
