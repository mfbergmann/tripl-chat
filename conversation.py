import whisper
import os
import openai

model = whisper.load_model("base")
result = model.transcribe("TDAudio.0.wav")
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