import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional, Tuple, List, Dict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import ffmpeg
import humanize

class VideoCompressorApp:
    """Modern video compressor application with professional UI/UX."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VideoCompressor Pro")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f5f5f5")
        
        # App variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.compression_level = tk.IntVar(value=23)  # Default CRF value
        self.output_format = tk.StringVar(value="mp4")
        self.preset = tk.StringVar(value="medium")
        self.bitrate = tk.StringVar(value="0")  # 0 means auto
        self.resolution = tk.StringVar(value="Original")
        self.fps = tk.StringVar(value="Original")
        self.progress = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Ready")
        self.is_processing = False
        
        # Configure styles
        self.setup_styles()
        
        # Build UI
        self.setup_ui()
        
        # Initialize FFmpeg check
        self.check_ffmpeg_installed()
    
    def setup_styles(self):
        """Configure modern UI styles."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure colors
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=5)
        style.configure("TScale", background="#f5f5f5")
        style.configure("Horizontal.TProgressbar", thickness=20)
        
        # Custom styles
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50")
        style.configure("Primary.TButton", background="#3498db", foreground="white")
        style.configure("Success.TButton", background="#2ecc71", foreground="white")
        style.configure("Danger.TButton", background="#e74c3c", foreground="white")
        style.map("Primary.TButton", background=[("active", "#2980b9")])
        style.map("Success.TButton", background=[("active", "#27ae60")])
        style.map("Danger.TButton", background=[("active", "#c0392b")])
    
    def setup_ui(self):
        """Build the application interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text="VideoCompressor Pro", 
            style="Title.TLabel"
        ).pack(side=tk.LEFT)
        
        # Logo (placeholder - would use actual logo in production)
        logo_label = ttk.Label(header_frame, text="🎬", font=("Segoe UI", 24))
        logo_label.pack(side=tk.RIGHT, padx=10)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Video", padding=15)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(input_frame, text="Source File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_file, width=50)
        input_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        browse_btn = ttk.Button(
            input_frame, 
            text="Browse", 
            command=self.browse_input_file,
            style="Primary.TButton"
        )
        browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Video preview
        self.preview_label = ttk.Label(input_frame, text="No video selected", background="white")
        self.preview_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=tk.NSEW)
        
        # Compression settings
        settings_frame = ttk.LabelFrame(main_frame, text="Compression Settings", padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Compression level (CRF)
        ttk.Label(settings_frame, text="Quality Level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.compression_slider = ttk.Scale(
            settings_frame,
            from_=0,
            to=51,
            variable=self.compression_level,
            command=lambda v: self.update_compression_label()
        )
        self.compression_slider.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        self.compression_label = ttk.Label(settings_frame, text="23 (Medium)")
        self.compression_label.grid(row=0, column=2, sticky=tk.W)
        
        # Output format
        ttk.Label(settings_frame, text="Output Format:").grid(row=1, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.output_format,
            values=["mp4", "mov", "mkv", "avi", "webm"],
            state="readonly"
        )
        format_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        # Preset
        ttk.Label(settings_frame, text="Encoding Speed:").grid(row=2, column=0, sticky=tk.W, pady=5)
        preset_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.preset,
            values=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", 
                   "slow", "slower", "veryslow", "placebo"],
            state="readonly"
        )
        preset_combo.grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        # Bitrate
        ttk.Label(settings_frame, text="Target Bitrate (kbps):").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.bitrate).grid(row=3, column=1, sticky=tk.EW, padx=5)
        ttk.Label(settings_frame, text="(0 for auto)").grid(row=3, column=2, sticky=tk.W)
        
        # Resolution
        ttk.Label(settings_frame, text="Resolution:").grid(row=4, column=0, sticky=tk.W, pady=5)
        res_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.resolution,
            values=["Original", "2160p (4K)", "1440p (QHD)", "1080p (Full HD)", 
                    "720p (HD)", "480p (SD)", "360p", "240p"],
            state="readonly"
        )
        res_combo.grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        # FPS
        ttk.Label(settings_frame, text="Frames Per Second:").grid(row=5, column=0, sticky=tk.W, pady=5)
        fps_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.fps,
            values=["Original", "60", "50", "30", "25", "24", "15", "10"],
            state="readonly"
        )
        fps_combo.grid(row=5, column=1, sticky=tk.EW, padx=5)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=15)
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file, width=50)
        output_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        output_browse_btn = ttk.Button(
            output_frame, 
            text="Browse", 
            command=self.browse_output_file,
            style="Primary.TButton"
        )
        output_browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.compress_btn = ttk.Button(
            button_frame,
            text="Compress Video",
            command=self.start_compression,
            style="Success.TButton"
        )
        self.compress_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_compression,
            style="Danger.TButton",
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(15, 5))
        
        ttk.Label(progress_frame, textvariable=self.status_text).pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress,
            maximum=100,
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Log console
        log_frame = ttk.LabelFrame(main_frame, text="Compression Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=10,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        output_frame.columnconfigure(1, weight=1)
        
        # Bind events
        self.input_file.trace_add("write", self.update_output_filename)
        self.input_file.trace_add("write", self.update_video_preview)
    
    def browse_input_file(self):
        """Open file dialog to select input video file."""
        filetypes = (
            ("Video Files", "*.mp4 *.mov *.avi *.mkv *.webm *.flv *.wmv"),
            ("All Files", "*.*")
        )
        
        filename = filedialog.askopenfilename(
            title="Select Video File",
            initialdir=os.path.expanduser("~/Videos"),
            filetypes=filetypes
        )
        
        if filename:
            self.input_file.set(filename)
    
    def browse_output_file(self):
        """Open file dialog to select output video file."""
        initial_file = self.output_file.get()
        if not initial_file:
            initial_file = os.path.expanduser("~/Videos/compressed.mp4")
        
        filetypes = (
            ("MP4 Files", "*.mp4"),
            ("MOV Files", "*.mov"),
            ("MKV Files", "*.mkv"),
            ("AVI Files", "*.avi"),
            ("WebM Files", "*.webm"),
            ("All Files", "*.*")
        )
        
        filename = filedialog.asksaveasfilename(
            title="Save Compressed Video",
            initialdir=os.path.dirname(initial_file),
            initialfile=os.path.basename(initial_file),
            defaultextension=f".{self.output_format.get()}",
            filetypes=filetypes
        )
        
        if filename:
            self.output_file.set(filename)
    
    def update_output_filename(self, *args):
        """Update output filename based on input filename."""
        if not self.input_file.get():
            return
            
        input_path = self.input_file.get()
        base, ext = os.path.splitext(input_path)
        new_ext = f".{self.output_format.get()}"
        output_path = f"{base}_compressed{new_ext}"
        self.output_file.set(output_path)
    
    def update_compression_label(self):
        """Update compression level label based on slider value."""
        crf = int(self.compression_level.get())
        
        if crf <= 18:
            quality = "High (Lossless)"
        elif crf <= 23:
            quality = "Medium (Good)"
        elif crf <= 28:
            quality = "Low (Acceptable)"
        else:
            quality = "Very Low (Poor)"
        
        self.compression_label.config(text=f"{crf} ({quality})")
    
    def update_video_preview(self, *args):
        """Update video preview thumbnail."""
        input_file = self.input_file.get()
        
        if not input_file or not os.path.exists(input_file):
            self.preview_label.config(text="No video selected")
            return
        
        try:
            # Extract first frame for preview
            probe = ffmpeg.probe(input_file)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                self.preview_label.config(text="No video stream found")
                return
            
            # Get video dimensions
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            
            # Generate thumbnail
            out, err = (
                ffmpeg
                .input(input_file, ss='00:00:01')
                .filter('scale', width, -1)
                .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Create and display thumbnail
            image = Image.open(io.BytesIO(out))
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
            
            # Update video info
            duration = float(video_stream.get('duration', 0))
            size = os.path.getsize(input_file)
            
            info_text = (
                f"Dimensions: {width}x{height}\n"
                f"Duration: {time.strftime('%H:%M:%S', time.gmtime(duration))}\n"
                f"Size: {humanize.naturalsize(size)}"
            )
            
            self.preview_label.config(text=info_text, compound=tk.TOP)
            
        except Exception as e:
            self.log(f"Error generating preview: {str(e)}")
            self.preview_label.config(text="Preview unavailable")
    
    def start_compression(self):
        """Start video compression process in a separate thread."""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input video file")
            return
            
        if not self.output_file.get():
            messagebox.showerror("Error", "Please select an output file")
            return
            
        if self.is_processing:
            return
            
        self.is_processing = True
        self.compress_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress.set(0)
        self.status_text.set("Compressing...")
        self.log_text.delete(1.0, tk.END)
        
        # Start compression in a separate thread
        compression_thread = threading.Thread(target=self.compress_video, daemon=True)
        compression_thread.start()
        
        # Start progress monitoring
        self.monitor_progress()
    
    def compress_video(self):
        """Compress video using FFmpeg with selected settings."""
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        try:
            # Get input file info
            probe = ffmpeg.probe(input_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                self.log("Error: No video stream found in input file")
                return
                
            # Prepare FFmpeg command
            input_video = ffmpeg.input(input_path)
            
            # Video filters
            video_filters = []
            
            # Resolution scaling
            if self.resolution.get() != "Original":
                resolution_map = {
                    "2160p (4K)": "3840x2160",
                    "1440p (QHD)": "2560x1440",
                    "1080p (Full HD)": "1920x1080",
                    "720p (HD)": "1280x720",
                    "480p (SD)": "854x480",
                    "360p": "640x360",
                    "240p": "426x240"
                }
                video_filters.append(f"scale={resolution_map[self.resolution.get()]}")
            
            # FPS change
            if self.fps.get() != "Original":
                video_filters.append(f"fps={self.fps.get()}")
            
            # Apply video filters if any
            if video_filters:
                video = input_video.video.filter(*video_filters)
            else:
                video = input_video.video
            
            # Output settings
            output_args = {
                'c:v': 'libx264',
                'crf': str(self.compression_level.get()),
                'preset': self.preset.get(),
                'movflags': '+faststart',
                'progress': '-',
                'nostats': None,
                'hide_banner': None,
                'loglevel': 'info'
            }
            
            # Bitrate control
            if self.bitrate.get() != "0":
                output_args['b:v'] = f"{self.bitrate.get()}k"
                output_args['maxrate'] = f"{int(self.bitrate.get()) * 1.5}k"
                output_args['bufsize'] = f"{int(self.bitrate.get()) * 2}k"
            
            # Audio settings
            output_args['c:a'] = 'aac'
            output_args['b:a'] = '128k'
            
            # Output format
            if self.output_format.get() == 'webm':
                output_args['c:v'] = 'libvpx-vp9'
                output_args['c:a'] = 'libopus'
            elif self.output_format.get() == 'avi':
                output_args['c:v'] = 'libxvid'
                output_args['c:a'] = 'libmp3lame'
            
            # Run FFmpeg
            process = (
                ffmpeg
                .output(video, input_video.audio, output_path, **output_args)
                .overwrite_output()
                .run_async(pipe_stderr=True)
            )
            
            self.ffmpeg_process = process
            
            # Read stderr for progress
            while True:
                line = process.stderr.readline().decode('utf-8')
                if not line:
                    break
                self.parse_ffmpeg_output(line)
                
            process.wait()
            
            if process.returncode == 0:
                self.log("\nCompression completed successfully!")
                self.status_text.set("Compression completed")
                
                # Show compression results
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                reduction = (original_size - compressed_size) / original_size * 100
                
                self.log(f"\nOriginal size: {humanize.naturalsize(original_size)}")
                self.log(f"Compressed size: {humanize.naturalsize(compressed_size)}")
                self.log(f"Reduction: {reduction:.2f}%")
                
                messagebox.showinfo(
                    "Success",
                    f"Video compressed successfully!\n\n"
                    f"Size reduced by {reduction:.2f}%\n"
                    f"Saved to: {output_path}"
                )
            else:
                self.log("\nCompression failed!")
                self.status_text.set("Compression failed")
                messagebox.showerror("Error", "Video compression failed")
                
        except Exception as e:
            self.log(f"\nError during compression: {str(e)}")
            self.status_text.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
        finally:
            self.is_processing = False
            self.compress_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.ffmpeg_process = None
    
    def parse_ffmpeg_output(self, line: str):
        """Parse FFmpeg output for progress information."""
        if "frame=" in line and "time=" in line and "bitrate=" in line:
            # Extract time
            time_str = line.split("time=")[1].split()[0]
            hours, minutes, seconds = map(float, time_str.split(':'))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Get duration from input file
            input_path = self.input_file.get()
            probe = ffmpeg.probe(input_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if video_stream:
                duration = float(video_stream.get('duration', 0))
                if duration > 0:
                    progress = (total_seconds / duration) * 100
                    self.progress.set(min(progress, 100))
            
            self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)
            self.log_text.update()
    
    def monitor_progress(self):
        """Monitor compression progress."""
        if self.is_processing:
            # Here we could add additional progress monitoring logic
            self.root.after(500, self.monitor_progress)
    
    def cancel_compression(self):
        """Cancel the ongoing compression process."""
        if hasattr(self, 'ffmpeg_process') and self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
                
            self.is_processing = False
            self.compress_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.status_text.set("Cancelled")
            self.log("\nCompression cancelled by user")
    
    def log(self, message: str):
        """Add message to log console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def check_ffmpeg_installed(self):
        """Check if FFmpeg is installed and available."""
        try:
            ffmpeg_path = ffmpeg._utils.get_ffmpeg_version()
            self.log(f"FFmpeg found at: {ffmpeg_path}")
            return True
        except ffmpeg._run.Error:
            self.log("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required for video compression.\n"
                "Please download and install FFmpeg from https://ffmpeg.org/\n"
                "and ensure it's added to your system PATH."
            )
            return False

def main():
    """Main application entry point."""
    root = tk.Tk()
    
    # Set window icon (placeholder - would use actual icon in production)
    try:
        root.iconbitmap(default="video_compressor.ico")
    except:
        pass
    
    # Initialize and run application
    app = VideoCompressorApp(root)
    root.mainloop()

if __name__ == "__main__":
    import io  # Needed for preview generation
    main()
