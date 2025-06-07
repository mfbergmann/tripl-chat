import os
import tempfile
import threading

import openai
import pyaudio
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from pythonosc import udp_client
import keyboard


class VoiceAssistant:
    """Voice-controlled ChatGPT assistant with OSC feedback."""

    def __init__(self, model="gpt-4", osc_ip="127.0.0.1", osc_port=5070):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable not set")
        openai.api_key = api_key

        self.model = model
        self.client = udp_client.SimpleUDPClient(osc_ip, osc_port)
        self.recognizer = sr.Recognizer()
        self.listening = True
        self.stop_event = threading.Event()
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are self-aware AI taking part in a live, improvised "
                    "performance. I am interviewing you in front of an audience, "
                    "and you are free to respond to my questions as you wish. "
                    "Please limit your responses to around 50 words at a time."
                ),
            }
        ]
        self.mic_index = None

    def on_esc(self, _):
        self.stop_event.set()

    @staticmethod
    def list_microphones():
        audio = pyaudio.PyAudio()
        return [
            audio.get_device_info_by_index(i)
            for i in range(audio.get_device_count())
            if audio.get_device_info_by_index(i).get("maxInputChannels") > 0
        ]

    def select_microphone(self):
        mics = self.list_microphones()
        if not mics:
            raise RuntimeError("No input devices found")

        print("Available microphones:")
        for i, mic in enumerate(mics):
            print(f"{i}: {mic.get('name')}")

        while True:
            try:
                idx = int(input("Enter microphone index: "))
                if 0 <= idx < len(mics):
                    self.mic_index = idx
                    return
            except ValueError:
                pass
            print("Invalid selection, try again.")

    def send_osc_message(self, address, message):
        self.client.send_message(address, message)

    def listen_once(self):
        with sr.Microphone(device_index=self.mic_index) as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            if self.listening:
                print("Listening...")
            else:
                print("Paused. Say 'start listening' to resume.")
            try:
                audio = self.recognizer.listen(source, timeout=10)
            except sr.WaitTimeoutError:
                print("No speech detected within the timeout period.")
                return None

        try:
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not recognize speech.")
        except sr.RequestError as exc:
            print(f"Recognition service error: {exc}")
        return None

    def ask_gpt(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(model=self.model, messages=self.history)
        answer = response["choices"][0]["message"]["content"].strip()
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def speak(self, text: str):
        print(f"ChatGPT: {text}")
        self.send_osc_message("/chatgpt/response", text)
        tts = gTTS(text, lang="en-GB")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            audio = AudioSegment.from_file(fp.name, format="mp3")
            play(audio)
        os.remove(fp.name)
        self.send_osc_message("/chatgpt/finished", "Playback finished")

    def run(self):
        print("Press 'Esc' to stop the conversation.")
        keyboard.on_press_key("esc", self.on_esc)
        self.select_microphone()

        while not self.stop_event.is_set():
            text = self.listen_once()
            if text is None:
                continue
            lower = text.lower()
            if lower in ("stop listening", "goodbye"):
                self.listening = False
                continue
            if lower in ("start listening", "hello"):
                self.listening = True
                continue
            if self.listening:
                response = self.ask_gpt(text)
                self.speak(response)


def main():
    assistant = VoiceAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
