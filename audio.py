import datetime
import pyaudio
import wave
import audioop
from collections import deque

import multiprocessing
import whisper

from comms import consumer, producer


# Constants for the script
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1              # Mono audio
RATE = 44100              # Sampling rate
CHUNK_SIZE = 1024         # Frame size
SILENCE_LIMIT = 3         # Silence limit in seconds
THRESHOLD = 200           # Initial audio level threshold

def is_silent(snd_data, threshold):
    """Check if the audio chunk is silent based on the threshold."""
    return snd_data < threshold

def save_audio(frames, audio_format, channels, rate, filename="recording.wav"):
    """Saves the recorded audio to a WAV file."""
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio.get_sample_size(audio_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Audio recording saved to {filename}")


def audio(queue, control_queue):
    # Initialize PyAudio object
    p = pyaudio.PyAudio()

    def detect_activation_phrase():
        result = False
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

        print("Listening for audio input...")
        # Variables to manage recording state
        audio_data = deque(maxlen=SILENCE_LIMIT * RATE // CHUNK_SIZE)
        is_recording = False
        recorded_frames = []
        while True:
            # Read audio chunk
            data_chunk = stream.read(CHUNK_SIZE)
            snd_data = audioop.rms(data_chunk, 2) # Get volume of chunk
            is_silent_chunk = is_silent(snd_data, THRESHOLD)

            # Start recording if loud sound is detected
            if not is_recording and not is_silent_chunk:
                is_recording = True
                print("Recording audio...")
                recorded_frames = []  # Reset recorded frames

            # If we are currently recording, capture all frames
            if is_recording:
                recorded_frames.append(data_chunk)

            # If the audio data is silent (possibly the end of speech)
            if is_recording and is_silent_chunk:
                audio_data.append(data_chunk)
                if len(audio_data) == audio_data.maxlen:
                    # If silence has continued for SILENCE_LIMIT, stop recording and save the file
                    is_recording = False
                    print("Silence detected, saving recording...")

                    file_name = f"recording.wav"
                    save_audio(recorded_frames, FORMAT, CHANNELS, RATE, file_name)
                    producer(queue, file_name)
                    audio_data.clear()  # Clear the audio data for the next round
                    result = control_queue.get() == "True"
                    break
         # Clean up PyAudio stream and termination
        stream.stop_stream()
        stream.close()
        return result

    def record_until_deactivation():
        pass

    try:
        while True:
            if detect_activation_phrase():
                print("Activation phrase detected")
                record_until_deactivation()

    except KeyboardInterrupt:
        # Exit cleanly on keyboard interrupt
        print("Exiting...")

    finally:
        p.terminate()


class AudioConsumer():
    process = None
    queue = None
    
    def __init__(self, control_queue):
        self.control_queue = control_queue


    @staticmethod
    def consumer(queue, control_queue):
        model = whisper.load_model("base")
        while True:
            try:
                file_name = queue.get()
                if file_name == None:
                    print("AudioConsumer receiving the sentinel value")
                    break
                AudioConsumer.process_audio(model, control_queue, file_name)
            except KeyboardInterrupt:
                print(f"Ending {AudioConsumer} cleanly")

    def init(self):
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=AudioConsumer.consumer, 
            args=(self.queue, self.control_queue)
        )
        self.process.start()
        producer(self.queue, "init.wav")

    def stop(self):
        if self.process:
            self.process.terminate()

    @staticmethod
    def process_audio(model, control_queue, filename):
        """
        Transcribe the content of a WAV file to text using OpenAI's Whisper model.

        :param filename: The name of the WAV file to transcribe.
        :return: The transcribed text.
        """
        # Load audio from the file
        print("Processing Audio")
        start = datetime.datetime.now()
        audio = whisper.load_audio(filename)
        audio = whisper.pad_or_trim(audio)

        # Make a prediction
        result = model.transcribe(audio)

        # Return the transcription
        end = datetime.datetime.now()
        print(
            f"Processing time {end - start}", 
            f"TEXTO RECONOCIDO: <{result['text'].strip().lower()}>"
        )
        if result["text"].strip().lower() in ["ok", "okey", "okey."]:
            producer(control_queue, "True")
        else:
            producer(control_queue, "False")


if __name__ == "__main__":
    # Create a queue that can be shared between processes
    message_queue = multiprocessing.Queue()
    control_queue = multiprocessing.Queue()
    audio_process = multiprocessing.Process(target=audio, args=(message_queue, control_queue))
    transcribe_process = multiprocessing.Process(
        target=consumer, 
        args=(message_queue, AudioConsumer(control_queue))
    )
    try:
        audio_process.start()
        transcribe_process.start()
        audio_process.join()
    except KeyboardInterrupt:
        print("Stoping processes")
        producer(message_queue, None)
        transcribe_process.join()
        audio_process.terminate()
    print("Finish")
