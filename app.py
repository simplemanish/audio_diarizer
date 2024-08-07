import streamlit as st
# from helper import uploaded_files, get_response, save_to_gcs, audio_mapping
from helper import get_response, save_to_gcs

st.title("Audio Bot")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mapping" not in st.session_state:
    st.session_state.mapping = dict()

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()

if "audio_mapping" not in st.session_state:
    st.session_state.audio_mapping = dict()
# if "uploader_visible" not in st.session_state:
#     st.session_state["uploader_visible"] = False

# def show_upload(state:bool):
#     st.session_state["uploader_visible"] = state

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

cols = st.columns(2)
cols_2 = st.columns(2)
audio = cols[0].file_uploader("Upload an audio file", type=["mp3", "wav"], on_change=None)

if audio is not None and audio.name not in st.session_state.uploaded_files:
    save_to_gcs(audio, st.session_state.uploaded_files, st.session_state.mapping, st.session_state.audio_mapping)

file_selected = cols[1].selectbox("Which Audio File you want to process?", st.session_state.uploaded_files)
is_audio = cols_2[0].checkbox('Perform Audio Analysis', key='is_audio', on_change=None)
if file_selected:
    cols_2[1].audio(st.session_state.audio_mapping[file_selected].getvalue())

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)


    with st.chat_message("assistant"):
        if is_audio and file_selected:
            response = st.write_stream(get_response(file_selected, prompt, st.session_state.mapping, True))
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            response = st.write_stream(get_response(file_selected, prompt, st.session_state.mapping, False))
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.download_button('Download Text', response)