import vlc
import threading
import socket

class VideoClient:
    """
    Basic class to manage the vlc instance
    """
    def __init__(self, stream_url):
        self.stream_url = stream_url
        self.instance = vlc.Instance("--no-xlib")
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(self.stream_url)
        self.media.get_mrl()
        self.player.set_media(self.media)

    def play_video(self):
        self.player.play()

    def start_playing(self):
        self.play_thread = threading.Thread(target=self.play_video)
        self.play_thread.start()

    def stop_playing(self):
        self.player.stop()

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            self.player.audio_set_volume(volume)
        else:
            print("Volume should be in the range 0 to 100.")

    def change_stream_url(self, new_stream_url):
        self.stop_playing()
        self.stream_url = new_stream_url
        self.media = self.instance.media_new(self.stream_url)
        self.media.get_mrl()
        self.player.set_media(self.media)
        self.start_playing()

    def listen(self, server_address, port):
        """
        Connect to server with socketio and listen for commands:
            - change volume
            - change channel
            - pause / play
            - etc
        """




if __name__ == "__main__":
    # Replace 'localhost' and '8080' with the actual host and port where the server is running
    initial_stream_url = "http://localhost:8080"
    video_client = VideoClient(initial_stream_url)

    # Start playing the initial video stream
    video_client.start_playing()

    # Adjust volume
    video_client.set_volume(50)

    # Wait for some time (you can adjust the duration as needed)
    input("Press Enter to change stream URL...")

    # Change the stream URL
    new_stream_url = "http://new-server:8080"  # Replace with the desired new URL
    video_client.change_stream_url(new_stream_url)

    # Wait for some time (you can adjust the duration as needed)
    input("Press Enter to stop playing...")

    # Stop playing the video stream
    video_client.stop_playing()
