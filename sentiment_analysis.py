from nltk.sentiment import SentimentIntensityAnalyzer
import nltk as nt
from pydub import AudioSegment
import io
import speech_recognition as sr


nt.download('vader_lexicon')

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    audio_file.seek(0)

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Audio unintelligible"
        except sr.RequestError as e:
            return f"Error with the request: {e}"
        
def analyze_sentiment(audio_file):
    if audio_file.type != 'audio/wav':
        audio = AudioSegment.from_file(audio_file)
        audio_file = io.BytesIO()
        audio.export(audio_file, format="wav")
        audio_file.seek(0)

    text = transcribe_audio(audio_file)

    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(text)

    return text, sentiment_scores
