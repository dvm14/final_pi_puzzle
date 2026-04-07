"""
voice.py — Threaded Text-to-Speech (TTS) announcer.

Uses the pyttsx3 library to generate voice prompts. Runs on a background daemon thread
with a message queue. This ensures that the text-to-speech engine can speak
without blocking the main game loop, keeping the LCD countdown and camera frames smooth.
"""

import pyttsx3
import threading
import queue

class VoiceAnnouncer:
    """
    Manages asynchronous Text-to-Speech operations.
    """

    def __init__(self):
        """
        Initialize the message queue and start the background worker thread.
        """
        # Create a thread-safe queue to hold the text strings we want to speak
        self._q = queue.Queue()
        
        # Initialize and start a background daemon thread
        # daemon=True ensures this thread will automatically exit when the main program stops
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """
        The background thread's main loop. It continuously waits for new text
        in the queue and reads it out loud using the pyttsx3 engine.
        """
        # Initialize the TTS engine inside the thread that will use it
        engine = pyttsx3.init()
        
        # Adjust the speaking rate (words per minute). 
        # Default is usually 200, which might be slightly too fast for instructions.
        engine.setProperty('rate', 160) 
        
        while True:
            # Block and wait until an item is available in the queue
            text = self._q.get()
            
            # A 'None' object acts as a poison pill to safely shut down the thread
            if text is None:
                self._q.task_done()
                break
                
            # Synthesize and play the speech
            engine.say(text)
            engine.runAndWait()
            
            # Mark the task as finished in the queue
            self._q.task_done()

    def speak(self, text: str):
        """
        Add a new text string to the speech queue. 
        Returns immediately without waiting for the speech to finish.
        
        Parameters
        ----------
        text : str
            The sentence to be spoken out loud.
        """
        self._q.put(text)

    def cleanup(self):
        """
        Safely shut down the background thread by sending a termination signal (None).
        Call this method during the main game shutdown process.
        """
        self._q.put(None)

# ---------------------------------------------------------------------------
# Standalone Testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    
    print("Testing VoiceAnnouncer... Press Ctrl+C to stop.")
    announcer = VoiceAnnouncer()
    
    try:
        # Test if the non-blocking behavior works
        announcer.speak("Face Happy. Left hand peace at Pink. Right hand thumbs up at Blue.")
        print("Command sent to queue! Main thread is not blocked.")
        
        # Simulate main thread doing other work (like updating LCD)
        for i in range(5):
            print(f"Main thread ticking... {i+1}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        announcer.cleanup()
        print("Announcer shut down safely.")