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
           
