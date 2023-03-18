import whisper
import os
import openai

import argparse

from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

from pythonosc import udp_client

model = whisper.load_model("base")


def sendOSC(filter, response):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="IP of the TD OSC")
    parser.add_argument("--port", type=int, default=5070, help="The port TD OSC is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    client.send_message(filter, response)


def transcribe(stream, val):
    result = model.transcribe("TDAudio.0.wav", fp16=False)
    text = result["text"]

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )

    file = open("transcript.txt", "a")
    file.write("\n")
    file.write(text)
    file.write("\n")
    file.write(response["choices"][0]["text"])
    file.close()

    sendOSC("/response", response["choices"][0]["text"])




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
        type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.map("/trigger", transcribe)

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print ("Serving on {}".format(server.server_address))
    server.serve_forever()

