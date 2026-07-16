import customtkinter as ctk
from tkinter import filedialog, Canvas
import cv2
from PIL import Image, ImageTk
import os
import threading
from moviepy import VideoFileClip
from proglog import ProgressBarLogger

# --- Custom Logger to capture real-time progress ---
class UIProgressBarLogger(ProgressBarLogger):
    def __init__(self, update_callback):
        super().__init__()
        # Renamed to update_callback to avoid clashing with proglog's internal message system
        self.update_callback = update_callback

    def bars_callback(self, bar, attr, value, old_value=None):
        # Calculates the percentage of the current processing phase
        if bar in self.bars and self.bars[bar]['total']:
            percent = (value / self.bars[bar]['total']) * 100
            self.update_callback(percent, bar)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VisualTrimmer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Visual MP4 Trimmer")
        self.geometry("900x500") 
        self.resizable(False, False)

        # State variables
        self.file_path = None
        self.duration = 0
        self.fps = 0
        self.timeline_width = 800
        self.timeline_height = 80
        self.handle_width = 15
        self.cancel_requested = False
        
        # Pixel tracking for handles
        self.start_x = 0
        self.end_x = self.timeline_width
        self.dragging = None
        self.thumbnails = []

        self.setup_ui()

    def setup_ui(self):
        # File Name Header
        self.header = ctk.CTkLabel(self, text="Select a video to generate timeline", font=ctk.CTkFont(size=18, weight="bold"))
        self.header.pack(pady=(20, 5))

        # --- Top Control Bar ---
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=5)

        self.load_btn = ctk.CTkButton(self.control_frame, text="Open .mp4", width=120, command=self.load_video)
        self.load_btn.grid(row=0, column=0, padx=10)

        self.refresh_btn = ctk.CTkButton(self.control_frame, text="Refresh UI", width=120, fg_color="#f39c12", hover_color="#d68910", command=self.refresh_app)
        self.refresh_btn.grid(row=0, column=1, padx=10)

        self.close_btn = ctk.CTkButton(self.control_frame, text="Close App", width=120, fg_color="#c0392b", hover_color="#a93226", command=self.close_app)
        self.close_btn.grid(row=0, column=2, padx=10)

        # --- Timeline Canvas ---
        self.canvas = Canvas(self, width=self.timeline_width, height=self.timeline_height, 
                             bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        self.canvas.bind("<Button-1>", self.click_handle)
        self.canvas.bind("<B1-Motion>", self.drag_handle)
        self.canvas.bind("<ButtonRelease-1>", self.release_handle)

        # --- Action Area ---
        self.trim_btn = ctk.CTkButton(self, text="Trim & Save", fg_color="#28a745", hover_color="#218838", 
                                      state="disabled", command=self.process_video)
        self.trim_btn.pack(pady=5)

        # Stop Button (Hidden by default)
        self.stop_btn = ctk.CTkButton(self, text="Stop Trimming", fg_color="#c0392b", hover_color="#a93226", command=self.stop_processing)
        
        # Progress Bar (Now set to determinate for live percentage tracking)
        self.progress_bar = ctk.CTkProgressBar(self, width=400, mode="determinate")
        self.progress_bar.set(0)
        
        # Status Label
        self.status = ctk.CTkLabel(self, text="", text_color="gray")
        self.status.pack(pady=5)

    def refresh_app(self):
        """Resets the UI back to a clean state"""
        self.file_path = None
        self.duration = 0
        self.thumbnails.clear()
        self.canvas.delete("all")
        self.header.configure(text="Select a video to generate timeline")
        self.status.configure(text="App refreshed.", text_color="gray")
        self.trim_btn.configure(state="disabled")
        
        # Hide progress elements
        self.progress_bar.pack_forget()
        self.stop_btn.pack_forget()

    def close_app(self):
        """Forcefully kills the app and any stuck background threads"""
        os._exit(0)

    def format_time(self, seconds):
        """Helper to convert raw seconds into HH:MM:SS or MM:SS format"""
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def update_status_text(self):
        if self.duration == 0:
            return

        start_sec = (self.start_x / self.timeline_width) * self.duration
        end_sec = (self.end_x / self.timeline_width) * self.duration
        selected_length = end_sec - start_sec

        status_text = (
            f"Selection: {self.format_time(start_sec)} to {self.format_time(end_sec)} | "
            f"New Length: {self.format_time(selected_length)} | "
            f"Original: {self.format_time(self.duration)}"
        )
        self.status.configure(text=status_text, text_color="white")

    def load_video(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("MP4 Files", "*.mp4")])
        if not self.file_path:
            return

        self.header.configure(text=os.path.basename(self.file_path))
        self.status.configure(text="Generating thumbnails...", text_color="white")
        self.update()

        self.generate_filmstrip()
        self.draw_timeline()
        self.trim_btn.configure(state="normal")
        self.update_status_text()

    def generate_filmstrip(self):
        cap = cv2.VideoCapture(self.file_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = total_frames / self.fps

        thumb_count = 8
        thumb_w = self.timeline_width // thumb_count
        self.thumbnails.clear()

        for i in range(thumb_count):
            frame_pos = int((i / thumb_count) * total_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((thumb_w, self.timeline_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.thumbnails.append(photo)

        cap.release()

        self.start_x = 0
        self.end_x = self.timeline_width

    def draw_timeline(self):
        self.canvas.delete("all")

        thumb_w = self.timeline_width // len(self.thumbnails) if self.thumbnails else 0
        for i, photo in enumerate(self.thumbnails):
            self.canvas.create_image(i * thumb_w, 0, image=photo, anchor="nw")

        self.canvas.create_rectangle(0, 0, self.start_x, self.timeline_height, fill="#111111", stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(self.end_x, 0, self.timeline_width, self.timeline_height, fill="#111111", stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(self.start_x, 0, self.end_x, self.timeline_height, outline="#9b59b6", width=3, tags="box")
        self.canvas.create_rectangle(self.start_x, 0, self.start_x + self.handle_width, self.timeline_height, fill="#9b59b6", outline="white", tags="start_handle")
        self.canvas.create_rectangle(self.end_x - self.handle_width, 0, self.end_x, self.timeline_height, fill="#9b59b6", outline="white", tags="end_handle")

    def click_handle(self, event):
        if abs(event.x - self.start_x) < self.handle_width * 2:
            self.dragging = "start"
        elif abs(event.x - self.end_x) < self.handle_width * 2:
            self.dragging = "end"

    def drag_handle(self, event):
        if not self.dragging: return

        x = max(0, min(event.x, self.timeline_width))
        if self.dragging == "start":
            self.start_x = min(x, self.end_x - self.handle_width * 2)
        elif self.dragging == "end":
            self.end_x = max(x, self.start_x + self.handle_width * 2)

        self.draw_timeline()
        self.update_status_text()

    def release_handle(self, event):
        self.dragging = None

    def stop_processing(self):
        self.cancel_requested = True
        self.status.configure(text="Trimming interrupted. UI Reset.", text_color="#f39c12")
        
        self.progress_bar.pack_forget()
        self.stop_btn.pack_forget()
        
        self.trim_btn.configure(state="normal")
        self.load_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")

    def _progress_callback(self, percent, bar_type):
        """Called by the background logger to update the UI thread"""
        if not self.cancel_requested:
            self.after(0, self._update_progress_ui, percent, bar_type)

    def _update_progress_ui(self, percent, bar_type):
        """Updates the physical progress bar and label"""
        self.progress_bar.set(percent / 100.0)
        
        # 'chunk' is MoviePy's internal name for the audio processing phase
        phase_name = "Audio" if bar_type == "chunk" else "Video"
        self.status.configure(text=f"Processing {phase_name}... {int(percent)}%", text_color="yellow")

    def process_video(self):
        if not self.file_path:
            return

        self.cancel_requested = False

        self.trim_btn.configure(state="disabled")
        self.load_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")

        self.stop_btn.pack(pady=(5, 0), before=self.status)
        
        # Reset progress bar to 0 before packing
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 5), before=self.status)

        self.status.configure(text="Preparing to trim...", text_color="yellow")

        start_time = (self.start_x / self.timeline_width) * self.duration
        end_time = (self.end_x / self.timeline_width) * self.duration

        dir_name = os.path.dirname(self.file_path)
        base_name = os.path.basename(self.file_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_trimmed{ext}")

        threading.Thread(
            target=self._trim_thread, 
            args=(start_time, end_time, output_path, name, ext), 
            daemon=True
        ).start()

    def _trim_thread(self, start_time, end_time, output_path, name, ext):
        try:
            video = VideoFileClip(self.file_path)
            new_video = video.subclipped(start_time, end_time)
            
            # Create our custom logger and pass it to write_videofile
            logger = UIProgressBarLogger(self._progress_callback)
            
            new_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=logger)
            
            video.close()
            new_video.close()

            if not self.cancel_requested:
                self.after(0, self._trim_success, name, ext)

        except Exception as e:
            if not self.cancel_requested:
                self.after(0, self._trim_error, str(e))

    def _trim_success(self, name, ext):
        self.progress_bar.pack_forget() 
        self.stop_btn.pack_forget()
        
        self.status.configure(text=f"Saved perfectly as:\n{name}_trimmed{ext}", text_color="#28a745")
        
        self.trim_btn.configure(state="normal")
        self.load_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")

    def _trim_error(self, error_message):
        self.progress_bar.pack_forget()
        self.stop_btn.pack_forget()
        
        self.status.configure(text=f"Error: {error_message}", text_color="red")
        
        self.trim_btn.configure(state="normal")
        self.load_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")

if __name__ == "__main__":
    app = VisualTrimmer()
    app.mainloop()