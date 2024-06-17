# TRiPL-Chat

TRiPL-Chat is a voice-controlled conversational assistant that uses ChatGPT, Google Text-to-Speech, and real-time audio streaming to create an interactive experience. Users can speak to the application, which transcribes the speech to text, sends the text to ChatGPT for processing, and plays back the generated response using text-to-speech.

## Features

- Voice input for a hands-free conversational experience
- Integration with OpenAI's ChatGPT for natural language understanding and generation
- Real-time audio streaming using Google Text-to-Speech
- OSC support for sending text messages to external applications

## Installation

1. Make sure you have Python 3.6 or higher installed. You can download Python [here](https://www.python.org/downloads/).

2. Clone this repository or download the source code.

3. Install the required dependencies by running the following command in the terminal or command prompt:

```bash
pip install -r requirements.txt
```

4.  Download FFmpeg for your operating system (Windows, macOS, or Linux) and add the bin folder to your system's PATH environment variable.

5.  Create an OpenAI API key and save it in a file named .env in the following format:

```
OPENAI_API_KEY=your_api_key_here
```

Replace your_api_key_here with your actual OpenAI API key.

## Usage
Run the conversation.py script using the following command:

```
python conversation.py
```

First you will be asked to choose your microphone from a numbered list. Then start speaking to the application, and it will transcribe your speech, send the text to ChatGPT, and play back the generated response using text-to-speech.

Press the Esc key at any time to stop the conversation. You can say "Stop Listening" or "Goodbye" to pause, and "Start Listening" or "Hello" to resume.

This version is currently using GPT-4 as the engine.

## Credits

TRiPL-Chat is a performance experiment running out of [TRiPL Lab.](https://tripl.ca)
