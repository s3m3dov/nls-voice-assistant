import pyttsx3

class VoiceAssistantTTS:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        
    def speak(self, text: str):
        """Speak the given text"""
        self.engine.say(text)
        self.engine.runAndWait()

# Test
if __name__ == "__main__":
    tts = VoiceAssistantTTS()
    tts.speak("Hello! This is a test of the text to speech system.")