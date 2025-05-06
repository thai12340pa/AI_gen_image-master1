import os
import threading
import logging
import tkinter as tk
from pathlib import Path
from typing import Optional
from PIL import Image, ImageTk

import customtkinter as ctk

from core.api_client import APIClient
from core.db import Database
from core.settings import ensure_dirs, DEFAULT_IMAGE_SIZE, API_PROVIDER, APP_CONFIG

logger = logging.getLogger(__name__)

class GenerateTab:
    """Tab for generating images from text prompts."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Use the new configuration system for API client initialization
        self.api_client = APIClient(
            api_key=APP_CONFIG.get("api_key", None),
            provider=APP_CONFIG.get("api_provider", None)
        )
        
        self.db = Database()
        self.frame = None
        self.preview_image = None
        self.generated_image = None
        self.generated_path = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI elements for the generate tab."""
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Input frame (top)
        input_frame = ctk.CTkFrame(self.frame)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Prompt label
        prompt_label = ctk.CTkLabel(
            input_frame,
            text="Prompt:",
            font=ctk.CTkFont(size=14)
        )
        prompt_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        # Prompt input
        self.prompt_var = ctk.StringVar()
        self.prompt_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.prompt_var,
            placeholder_text="Describe the image you want to generate...",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.prompt_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.prompt_entry.bind("<Return>", lambda event: self._on_generate())  # Bind Enter key to generate
        
        # Negative prompt label
        neg_prompt_label = ctk.CTkLabel(
            input_frame,
            text="Negative Prompt:",
            font=ctk.CTkFont(size=14)
        )
        neg_prompt_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        # Negative prompt input
        self.neg_prompt_var = ctk.StringVar()
        self.neg_prompt_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.neg_prompt_var,
            placeholder_text="Elements to avoid in the image (optional)",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.neg_prompt_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Size selection
        size_label = ctk.CTkLabel(
            input_frame,
            text="Size:",
            font=ctk.CTkFont(size=14)
        )
        size_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        # Get appropriate size options for the current provider
        self.size_var = ctk.StringVar()
        
        self.size_options = self._get_size_options_for_provider(self.api_client.provider)
        self.size_var.set(self.size_options[0])  # Default to first option
        
        self.size_dropdown = ctk.CTkOptionMenu(
            input_frame,
            variable=self.size_var,
            values=self.size_options
        )
        self.size_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Generate button
        generate_btn = ctk.CTkButton(
            input_frame,
            text="Generate",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=35,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._on_generate
        )
        generate_btn.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
        # Preview frame (center)
        preview_frame = ctk.CTkFrame(self.frame)
        preview_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Preview canvas
        self.canvas = tk.Canvas(
            preview_frame,
            bg="#2B2B2B" if ctk.get_appearance_mode() == "dark" else "#EBEBEB",
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Action buttons frame (bottom)
        action_frame = ctk.CTkFrame(self.frame)
        action_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=0)

        # Status label
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="Enter a prompt and click Generate",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Loading bar
        self.loading_bar = ctk.CTkProgressBar(action_frame, mode="determinate", width=300)
        self.loading_bar.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # Progress percentage label
        self.progress_var = tk.StringVar(value="Loading...")
        self.progress_label = ctk.CTkLabel(
            action_frame,
            textvariable=self.progress_var,
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")
    
    def _get_size_options_for_provider(self, provider):
        """Get size options based on the provider."""
        if provider == "openai":
            return ["256x256", "512x512", "1024x1024"]
        elif provider == "stability":
            return [
                "1024x1024",
                "1152x896",
                "1216x832",
                "1344x768",
                "1536x640",
                "768x1344",
                "832x1216",
                "896x1152"
            ]
        else:
            return [f"{DEFAULT_IMAGE_SIZE}x{DEFAULT_IMAGE_SIZE}"]
    
    def update_size_options(self, provider):
        """Update size options based on the selected provider."""
        self.size_options = self._get_size_options_for_provider(provider)
        self.size_var.set(self.size_options[0])  # Set default value
        self.size_dropdown.configure(values=self.size_options)
    
    def _on_generate(self):
        """Handle generate button click."""
        prompt = self.prompt_var.get().strip()
        if not prompt:
            self.main_window.show_error("Error", "Please enter a prompt")
            return
        
        # Disable UI during generation
        self._set_ui_state(False)
        self.status_label.configure(text="Generating image...")
        self.main_window.set_status("Generating image...")
        
        # Show loading bar
        self.loading_bar.grid()
        self.loading_bar.start()
        
        # Parse size
        size_str = self.size_var.get()
        width, height = map(int, size_str.split("x"))
        
        # Get negative prompt if any
        negative_prompt = self.neg_prompt_var.get().strip() or None
        
        # Start generation in a separate thread to keep UI responsive
        thread = threading.Thread(
            target=self._generate_image_thread,
            args=(prompt, (width, height), negative_prompt)
        )
        thread.daemon = True
        thread.start()

    def _set_ui_state(self, enabled):
        """Enable or disable UI elements."""
        state = "normal" if enabled else "disabled"
        self.prompt_entry.configure(state=state)
        self.neg_prompt_entry.configure(state=state)
        self.size_dropdown.configure(state=state)

    def _generate_image_thread(self, prompt, size, negative_prompt=None):
        """Generate image in a background thread."""
        try:
            # Kiểm tra kích thước hợp lệ
            valid_sizes = self._get_size_options_for_provider(self.api_client.provider)
            size_str = f"{size[0]}x{size[1]}"
            if size_str not in valid_sizes:
                raise ValueError(f"Invalid size {size_str}. Allowed sizes: {', '.join(valid_sizes)}")
            
            # Gọi API để tạo hình ảnh
            logger.info("Sending request to API...")
            image = self.api_client.generate_image(
                prompt=prompt,
                size=size,
                negative_prompt=negative_prompt
            )
            
            if image is None:
                raise ValueError("Failed to generate image. API returned None.")
            
            # Lưu hình ảnh vào thư mục `generated_images`
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            save_dir = os.path.join(base_dir, "generated_images")
            os.makedirs(save_dir, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
            
            # Tạo tên file dựa trên prompt và kích thước
            image_filename = f"{prompt.replace(' ', '_')[:50]}_{size[0]}x{size[1]}.png"
            image_path = os.path.join(save_dir, image_filename)
            
            # Lưu ảnh
            image.save(image_path)
            logger.info(f"Image saved to: {image_path}")
            
            # Cập nhật giao diện với hình ảnh mới
            self.frame.after(0, lambda: self._update_preview(image_path))
            self.frame.after(0, lambda: self._set_ui_state(True))
            self.frame.after(0, lambda: self.status_label.configure(text="Image generated successfully"))
            self.frame.after(0, lambda: self.main_window.set_status("Image generated successfully"))
        except Exception as e:
            logger.exception("Error generating image")
            self.frame.after(0, lambda: self._set_ui_state(True))
            self.frame.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)}"))
            self.frame.after(0, lambda: self.main_window.set_status(f"Error: {str(e)}"))
        finally:
            # Hide loading bar
            self.frame.after(0, lambda: self.loading_bar.stop())
            self.frame.after(0, lambda: self.loading_bar.grid_remove())

    def _update_preview(self, image_path):
        """Update the preview with the generated image."""
        # Clear canvas
        self.canvas.delete("all")
        
        # Open image from path and display
        try:
            image = Image.open(image_path)
            image.thumbnail((512, 512))  # Resize image to fit canvas
            self.preview_image = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.preview_image)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logger.exception(f"Failed to load image: {str(e)}")
            self.status_label.configure(text="Failed to load image.")
    
    def show(self):
        """Show this tab."""
        self.frame.grid(row=0, column=0, sticky="nsew")
    
    def hide(self):
        """Hide this tab."""
        self.frame.grid_forget()