import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import logging
import platform
import subprocess
import time  # Thêm thư viện để xử lý thời gian
from typing import Optional

logger = logging.getLogger(__name__)

class HistoryTab(ctk.CTkFrame):
    """Tab for viewing and managing image generation history."""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.history_frames = []
        
        # Create layout
        self._create_widgets()
        
        # Initially hidden
        self.hide()
        
    def _create_widgets(self):
        """Create and configure widgets."""
        # Top controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.refresh_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Refresh", 
            width=100,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self.refresh
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Scrollable frame for history items
        self.history_container = ctk.CTkScrollableFrame(self)
        self.history_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def refresh(self):
        """Refresh the history list."""
        # Clear existing items
        for frame in self.history_frames:
            frame.destroy()
        self.history_frames = []

        # Automatically determine the path to the `generated_images` folder
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Current file's directory
        image_dir = os.path.join(base_dir, "..", "generated_images")  # Path to `generated_images`

        # Ensure the directory exists
        if not os.path.exists(image_dir):
            logger.warning(f"Directory not found: {image_dir}")
            no_items_label = ctk.CTkLabel(
                self.history_container,
                text="No history items found.",
                font=("Arial", 14),
                text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey"
            )
            no_items_label.pack(pady=20)
            self.history_frames.append(no_items_label)
            return

        # Get all image files in the directory
        image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # If no images found, show a message
        if not image_files:
            no_items_label = ctk.CTkLabel(
                self.history_container,
                text="No history items found.",
                font=("Arial", 14),
                text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey"
            )
            no_items_label.pack(pady=20)
            self.history_frames.append(no_items_label)
            return

        # Display each image
        for i, filepath in enumerate(image_files):
            frame = self._create_history_item(filepath, i)
            frame.pack(fill=tk.X, expand=True, pady=5)
            self.history_frames.append(frame)
    
    def _create_history_item(self, filepath: str, index: int) -> ctk.CTkFrame:
        """Create a history item widget."""
        frame = ctk.CTkFrame(self.history_container)
        
        # Container for image and info
        content_frame = ctk.CTkFrame(frame)
        content_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        # Try to load the thumbnail
        try:
            if os.path.exists(filepath):
                img = Image.open(filepath)
                # Resize for thumbnail
                img.thumbnail((150, 150))
                img_tk = ImageTk.PhotoImage(img)
                
                # Image display
                img_label = tk.Label(content_frame, image=img_tk, bg="#484747" if ctk.get_appearance_mode().lower() == "dark" else "#DFDEDE")
                img_label.image = img_tk  # Keep a reference
                img_label.pack(side=tk.LEFT, padx=10, pady=10)
            else:
                # If file is missing, show placeholder
                missing_label = ctk.CTkLabel(
                    content_frame,
                    text="Image\nFile\nMissing",
                    font=("Arial", 12),
                    width=150,
                    height=150,
                    text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey"
                )
                missing_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        except Exception as e:
            logger.error(f"Error loading history image: {e}")
            error_label = ctk.CTkLabel(
                content_frame,
                text="Error\nLoading\nImage",
                font=("Arial", 12),
                width=150,
                height=150,
                text_color="red"
            )
            error_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Info frame
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Filepath
        filepath_label = ctk.CTkLabel(
            info_frame,
            text=f"File: {os.path.basename(filepath)}",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        filepath_label.pack(anchor="w")
        
        # Get file creation time
        creation_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(filepath)))
        creation_time_label = ctk.CTkLabel(
            info_frame,
            text=f"Created: {creation_time}",
            font=("Arial", 10),
            text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey",
            anchor="w"
        )
        creation_time_label.pack(anchor="w", pady=5)
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(info_frame)
        buttons_frame.pack(anchor="w", pady=5)
        
        open_btn = ctk.CTkButton(
            buttons_frame,
            text="View",
            width=80,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=lambda: self._on_open(filepath)
        )
        open_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            width=80,
            fg_color=["#D32F2F", "#D32F2F"],
            hover_color=["#B71C1C", "#B71C1C"],
            command=lambda: self._on_delete(filepath)
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        return frame
    
    def _on_open(self, filepath: str):
        """Open the image file."""
        if os.path.exists(filepath):
            # Use the system's default application to open the file
            logger.debug(f"Opening file: {filepath}")
            
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux
                subprocess.call(('xdg-open', filepath))
        else:
            logger.warning(f"File not found: {filepath}")
            # Show error message
            messagebox.showerror(
                "Error",
                f"The file {filepath} does not exist."
            )
    
    def _on_delete(self, filepath: str):
        """Delete an image from history."""
        # Confirm delete
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this image?"
        ):
            return
        
        # Delete the file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.debug(f"Deleted file: {filepath}")
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
                messagebox.showerror("Error", f"Failed to delete file: {e}")
        
        # Refresh the list
        self.refresh()
    
    def show(self):
        """Show this tab and refresh the content."""
        self.grid(row=0, column=0, sticky="nsew")
        self.refresh()  # Load latest entries
    
    def hide(self):
        """Hide this tab."""
        self.grid_forget()