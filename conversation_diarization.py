import os
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

diarize_text = ""


class ConversationDiarization:
    """
    Generate conversation diarization result.
    """

    def __init__(self, audio_file="", language="en-US", phrase_list=[]):
        self.audio_file = audio_file
        self.language = language
        self.phrase_list = phrase_list

    def conversation_transcriber_recognition_canceled_cb(self, evt: speechsdk.SessionEventArgs):
        print('Canceled event {}'.format(evt))
        print('Canceled event')

    def conversation_transcriber_session_stopped_cb(self, evt: speechsdk.SessionEventArgs):
        print('SessionStopped event')

    def conversation_transcriber_transcribed_cb(self, evt: speechsdk.SpeechRecognitionEventArgs):
        global diarize_text
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            diarize_text += evt.result.text + \
                "\t\n speaker ("+evt.result.speaker_id+")"
            print('\tText={}'.format(evt.result.text))
            print('\tSpeaker ID={}'.format(evt.result.speaker_id))
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print('\tNOMATCH: Speech could not be TRANSCRIBED: {}'.format(
                evt.result.no_match_details))

    def conversation_transcriber_session_started_cb(self, evt: speechsdk.SessionEventArgs):
        print('SessionStarted event')

    def recognize_from_file(self):
        load_dotenv()
        speech_config = speechsdk.SpeechConfig(subscription=os.getenv(
            'SPEECH_KEY'), region=os.getenv('SPEECH_REGION'),
            speech_recognition_language=self.language)

        audio_config = speechsdk.audio.AudioConfig(
            filename=self.audio_file)

        conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=speech_config, audio_config=audio_config)

        phrase_list_grammar = speechsdk.PhraseListGrammar.from_recognizer(
            conversation_transcriber)

        for phrase in self.phrase_list:
            phrase_list_grammar.addPhrase(phrase)

        transcribing_stop = False

        def stop_cb(evt: speechsdk.SessionEventArgs):
            # """callback that signals to stop continuous recognition upon
            # receiving an event `evt`"""
            # print('CLOSING on {}'.format(evt))
            nonlocal transcribing_stop
            transcribing_stop = True

        # Connect callbacks to the events fired by the conversation transcriber
        conversation_transcriber.transcribed.connect(
            self.conversation_transcriber_transcribed_cb)
        conversation_transcriber.session_started.connect(
            self.conversation_transcriber_session_started_cb)
        conversation_transcriber.session_stopped.connect(
            self.conversation_transcriber_session_stopped_cb)
        conversation_transcriber.canceled.connect(
            self.conversation_transcriber_recognition_canceled_cb)
        # stop transcribing on either session stopped or canceled events

        conversation_transcriber.session_stopped.connect(stop_cb)
        conversation_transcriber.canceled.connect(stop_cb)

        conversation_transcriber.start_transcribing_async()

        # Waits for completion.
        while not transcribing_stop:
            time.sleep(.5)
        conversation_transcriber.stop_transcribing_async()

        if transcribing_stop:y
            return diarize_text


# Main
# if __name__ == "__main__":
#     main()

# try:
#     diarize = ConversationDiarization(
#         audio_file="C:/Users/047929/AppData/Local/Temp/tmp_oy133on.wav", language="en-US")
#     diarize.recognize_from_file()
# except Exception as err:
#     print("Encountered exception. {}".format(err))
