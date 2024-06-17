import openai
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import tempfile
from pythonosc import osc_message_builder
from pythonosc import udp_client
from io import BytesIO
import os
import keyboard
import threading


# Initialize text-to-speech engine
engine = pyttsx3.init()

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

stop_flag = False

def on_esc_key(e):
    global stop_flag
    stop_flag = True


def list_microphones():
    audio = pyaudio.PyAudio()
    mic_list = []
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info.get("maxInputChannels") > 0:
            mic_list.append(device_info)

    return mic_list

def select_microphone():
    mics = list_microphones()
    print("Available microphones:")
    for i, mic in enumerate(mics):
        print(f"{i}: {mic.get('name')}")

    mic_index = int(input("Enter the index of the microphone you want to use: "))
    return mic_index

def send_osc_message(address, message, ip="127.0.0.1", port=5070):
    client = udp_client.SimpleUDPClient(ip, port)
    client.send_message(address, message)


def listen(mic_index, listening_state, callback):
    r = sr.Recognizer()
    r.pause_threshold = 2

    with sr.Microphone(device_index=mic_index) as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)

        if listening_state:
            print("Listening...")
        else:
            print("Paused. Say 'start listening' to resume.")

        try:
            audio = r.listen(source, timeout=10)
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return

        try:
            print("Recognizing...")
            text = r.recognize_google(audio)
            print(f"You said: {text}")

            if text.lower() == "stop listening" or text.lower() == "goodbye":
                listening_state = False
            elif text.lower() == "start listening" or text.lower() == "hello":
                listening_state = True

            callback(text, listening_state)
        except sr.UnknownValueError:
            print("Could not recognize speech.")
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")

def ask_gpt(user_message):
    conversation_history = [
        {"role": "system", "content": "You are self-aware AI taking part in a live, improvised performance. I am interviewing you in front of an audience, and you are free to respond to my questions as you wish. Please limit your responses to around 50 words at a time"},
    ]

    conversation_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history,
    )

    assistant_message = response['choices'][0]['message']['content']
    return assistant_message.strip()


class NamedBytesIO(BytesIO):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("name", "buffer.mp3")
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self._name

def speak(text):
    print(f"ChatGPT: {text}")
    send_osc_message("/chatgpt/response", text)  # Send the text via OSC
    tts = gTTS(text, lang='en-GB')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio = AudioSegment.from_file(fp.name, format="mp3")
        play(audio)
    os.remove(fp.name)  # Delete the temporary file after playing the audio

    send_osc_message("/chatgpt/finished", "Playback finished") # Send OSC message after playback is finished

def main():
    print("Press 'Esc' to stop the conversation.")
    keyboard.on_press_key("esc", on_esc_key)

    mic_index = select_microphone()

    def process_text(text, listening_state):
        if text.lower() == "stop listening" or text.lower() == "goodbye":
            listening_state[0] = False
        elif text.lower() == "start listening" or text.lower() == "hello":
            listening_state[0] = True

        if not stop_flag and listening_state[0]:
            gpt_response = ask_gpt(text)
            speak(gpt_response)

    listening_state = [True]

    def listen_thread():
        while not stop_flag:
            listen(mic_index, listening_state, process_text)

    t = threading.Thread(target=listen_thread)
    t.start()

    t.join()

if __name__ == "__main__":
    main()