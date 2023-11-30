import pyaudio
import wave
import audioop
import math
from collections import deque

# Constants for the script
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1              # Mono audio
RATE = 44100              # Sampling rate
CHUNK_SIZE = 1024         # Frame size
SILENCE_LIMIT = 3         # Silence limit in seconds
THRESHOLD = 200           # Initial audio level threshold

def is_silent(snd_data, threshold):
    """Check if the audio chunk is silent based on the threshold."""
    print("Audio volume: ", snd_data)
    return snd_data < threshold

def save_audio(frames, audio_format, channels, rate):
    """Saves the recorded audio to a WAV file."""
    filename = "recording.wav"
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio.get_sample_size(audio_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Audio recording saved to {filename}")

def main():
    # Initialize PyAudio object
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    print("Listening for audio input...")

    # Variables to manage recording state
    audio_data = deque(maxlen=SILENCE_LIMIT * RATE // CHUNK_SIZE)
    is_recording = False
    recorded_frames = []

    try:
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
                    save_audio(recorded_frames, FORMAT, CHANNELS, RATE)
                    audio_data.clear()  # Clear the audio data for the next round

    except KeyboardInterrupt:
        # Exit cleanly on keyboard interrupt
        print("Exiting...")

    finally:
        # Clean up PyAudio stream and termination
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
