import os
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

diarize_text = ""
last_speaker_id = None


class ConversationDiarization:
    """
    Generate conversation diarization result.
    """

    def __init__(self, audio_file="", language="en-US", phrase_list=[]):
        self.audio_file = audio_file
        self.language = language
        self.phrase_list = phrase_list
        self.segments = []

    def conversation_transcriber_recognition_canceled_cb(self, evt: speechsdk.SessionEventArgs):
        print('Canceled event {}'.format(evt))
        print('Canceled event')

    def conversation_transcriber_session_stopped_cb(self, evt: speechsdk.SessionEventArgs):
        print('SessionStopped event')

    def conversation_transcriber_transcribed_cb(self, evt: speechsdk.SpeechRecognitionEventArgs):
        global diarize_text

        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            if evt.result.speaker_id and evt.result.speaker_id != "Unknown":
                # calculate start end time, convert into second.
                start_time = getFormattedTime(evt.result._offset/10000000)
                end_time = getFormattedTime(
                    (evt.result._offset + evt.result.duration)/10000000)
                self.segments.append({
                    'speaker_id': evt.result.speaker_id,
                    'text': evt.result.text,
                    'start_time': start_time,
                    'end_time': end_time
                })
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print('\tNOMATCH: Speech could not be TRANSCRIBED: {}'.format(
                evt.result.no_match_details))

    def conversation_transcriber_session_started_cb(self, evt: speechsdk.SessionEventArgs):
        print('SessionStarted event')
        global diarize_text
        diarize_text = ""
        self.segments = []

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
            """
            callback that signals to stop continuous recognition upon
            receiving an event `evt`
            """

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

        if transcribing_stop:
            diarize_text = ""
            last_speaker_id = None
            speaker_list = []
            for segment in self.segments:
                if last_speaker_id is None:
                    # For the first segment, start with "Guest-X:"
                    speaker_list.append([segment['speaker_id'], segment['start_time'], segment['end_time'], segment['text']])
                elif segment['speaker_id'] == last_speaker_id:
                    s_list = speaker_list[-1]
                    s_list[2] = segment['end_time']
                    s_list[3]+=segment['text']
                    speaker_list[-1] = s_list
                else:
                    # If the speaker changes, add a new entry with "Guest-X:"
                    if segment['text']:
                        speaker_list.append([segment['speaker_id'], segment['start_time'], segment['end_time'], segment['text']])
                last_speaker_id = segment['speaker_id']
            for talk in speaker_list:
                diarize_text+= f"{talk[0]} ({talk[1]}-{talk[2]}): {talk[3]}\n"
            return diarize_text


def getFormattedTime(seconds=0):
    s_min, s_sec = divmod(seconds, 60)
    # s_hr, s_min = divmod(s_min, 60)
    return "%0d:%02d" % (s_min, s_sec)


