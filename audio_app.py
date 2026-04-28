import customtkinter as ctk
from tkinter import filedialog, messagebox
import wave
import struct
import os
import threading
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

MAGIC = b"STEG"
SALT_SIZE = 16
HEADER_FMT = ">4s16sQ"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
FONT_NAME = ("Arial", 12)


def derive_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_message(password: str, message: str):
    salt = os.urandom(SALT_SIZE)
    key = derive_fernet_key(password, salt)
    cipher = Fernet(key)
    encrypted = cipher.encrypt(message.encode("utf-8"))
    return encrypted, salt


def decrypt_message(password: str, encrypted_bytes: bytes, salt: bytes) -> str:
    key = derive_fernet_key(password, salt)
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_bytes).decode("utf-8")


def calculate_capacity_bytes(wav_path: str) -> int:
    with wave.open(wav_path, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        return len(frames) // 8


def hide_bytes_in_wav(input_wav: str, output_wav: str, payload_bytes: bytes, progress_callback=None):
    with wave.open(input_wav, "rb") as src:
        params = src.getparams()
        frames = bytearray(src.readframes(src.getnframes()))

    total_bits = len(payload_bytes) * 8
    capacity_bits = len(frames)

    if total_bits > capacity_bits:
        raise ValueError("Payload too large for this audio file.")

    bits = "".join(format(b, "08b") for b in payload_bytes)

    for i, bit in enumerate(bits):
        frames[i] = (frames[i] & 0xFE) | int(bit)
        if progress_callback and i % 5000 == 0:
            progress_callback(i / total_bits)

    with wave.open(output_wav, "wb") as out:
        out.setparams(params)
        out.writeframes(bytes(frames))

    if progress_callback:
        progress_callback(1.0)


def extract_bytes_from_wav(input_wav: str, progress_callback=None):
    with wave.open(input_wav, "rb") as src:
        frames = bytearray(src.readframes(src.getnframes()))

    def read_n_bytes_from_bits(bit_offset: int, n_bytes: int):
        bits = []
        end_bit = bit_offset + n_bytes * 8
        for i in range(bit_offset, end_bit):
            bits.append(str(frames[i] & 1))
            if progress_callback and i % 5000 == 0:
                progress_callback((i - bit_offset) / (n_bytes * 8))
        return bytes(int("".join(bits[i:i + 8]), 2) for i in range(0, len(bits), 8))

    header_bytes = read_n_bytes_from_bits(0, HEADER_SIZE)

    try:
        magic, salt, enc_len = struct.unpack(HEADER_FMT, header_bytes)
    except Exception as e:
        raise ValueError("Invalid or missing header in audio file.") from e

    if magic != MAGIC:
        raise ValueError("No compatible hidden data found (magic mismatch).")

    encrypted_bytes = read_n_bytes_from_bits(HEADER_SIZE * 8, enc_len)

    if progress_callback:
        progress_callback(1.0)

    return salt, encrypted_bytes


class AudioStegApp(ctk.CTkFrame):
    def __init__(self, master, back_callback=None):
        super().__init__(master, fg_color="#ffe6f0")
        self.back_callback = back_callback

        self.selected_wav_path = None
        self.output_wav_path = None

        self.message_box = None
        self.password_entry = None
        self.show_pw_btn = None
        self.selected_path_label = None
        self.output_path_label = None
        self.status_label = None

        self.build_ui()

    def go_back(self):
        if self.back_callback:
            self.back_callback()

    def ui(self, func, *args, **kwargs):
        self.after(0, lambda: func(*args, **kwargs))

    def build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="#ffd6eb")
        top_frame.pack(fill="x", padx=16, pady=(12, 6))

        title_label = ctk.CTkLabel(
            top_frame,
            text="Audio Steganography",
            font=("Arial", 18, "bold"),
            text_color="#660033"
        )
        title_label.pack(side="left", padx=(6, 12), pady=8)

        btn_frame = ctk.CTkFrame(top_frame, fg_color="#ffd6eb")
        btn_frame.pack(side="right", padx=6)

        ctk.CTkButton(
            btn_frame,
            text="About",
            width=90,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.show_about
        ).grid(row=0, column=0, padx=6)

        ctk.CTkButton(
            btn_frame,
            text="Clear Fields",
            width=110,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.clear_fields
        ).grid(row=0, column=1, padx=6)

        middle_frame = ctk.CTkFrame(self, fg_color="#ffe6f0")
        middle_frame.pack(fill="both", expand=True, padx=16, pady=6)

        left_frame = ctk.CTkFrame(middle_frame, fg_color="#ffd6eb")
        left_frame.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=6)

        msg_label = ctk.CTkLabel(
            left_frame,
            text="Secret Message",
            font=FONT_NAME,
            text_color="#660033"
        )
        msg_label.pack(anchor="w", padx=6, pady=(6, 4))

        self.message_box = ctk.CTkTextbox(
            left_frame,
            width=520,
            height=220,
            font=FONT_NAME,
            fg_color="#fff0f5",
            text_color="#660033"
        )
        self.message_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        right_frame = ctk.CTkFrame(middle_frame, width=260, fg_color="#ffd6eb")
        right_frame.pack(side="right", fill="y", padx=(12, 6), pady=6)

        file_label = ctk.CTkLabel(
            right_frame,
            text="Audio File (WAV only)",
            font=FONT_NAME,
            text_color="#660033"
        )
        file_label.pack(anchor="w", padx=8, pady=(8, 4))

        ctk.CTkButton(
            right_frame,
            text="Select WAV File",
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.select_wav
        ).pack(fill="x", padx=8, pady=(0, 8))

        self.selected_path_label = ctk.CTkLabel(
            right_frame,
            text="No file selected",
            font=FONT_NAME,
            wraplength=230,
            anchor="w",
            text_color="#660033"
        )
        self.selected_path_label.pack(fill="x", padx=8, pady=(0, 8))

        self.output_path_label = ctk.CTkLabel(
            right_frame,
            text="Output: -",
            font=FONT_NAME,
            wraplength=230,
            anchor="w",
            text_color="#660033"
        )
        self.output_path_label.pack(fill="x", padx=8, pady=(0, 8))

        pass_label = ctk.CTkLabel(
            right_frame,
            text="Encryption Password",
            font=FONT_NAME,
            text_color="#660033"
        )
        pass_label.pack(anchor="w", padx=8, pady=(8, 4))

        pw_frame = ctk.CTkFrame(right_frame, fg_color="#ffd6eb")
        pw_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.password_entry = ctk.CTkEntry(
            pw_frame,
            placeholder_text="Enter password",
            show="*",
            fg_color="#fff0f5",
            text_color="#660033",
            placeholder_text_color="#aa6688"
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.show_pw_btn = ctk.CTkButton(
            pw_frame,
            text="Show",
            width=60,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.toggle_password
        )
        self.show_pw_btn.pack(side="right")

        actions_frame = ctk.CTkFrame(self, fg_color="#ffd6eb")
        actions_frame.pack(fill="x", padx=16, pady=(8, 4))

        ctk.CTkButton(
            actions_frame,
            text="Hide Message",
            width=160,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.on_hide_clicked
        ).pack(side="left", padx=(20, 12), pady=8)

        ctk.CTkButton(
            actions_frame,
            text="Extract Message",
            width=160,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            command=self.on_extract_clicked
        ).pack(side="left", padx=12, pady=8)

        self.status_label = ctk.CTkLabel(
            self,
            text="Status: Ready",
            font=FONT_NAME,
            anchor="w",
            text_color="#cc6699"
        )
        self.status_label.pack(fill="x", padx=18, pady=(6, 12))

        bottom_frame = ctk.CTkFrame(self, fg_color="#ffd6eb")
        bottom_frame.pack(fill="x", padx=16, pady=(4, 12))

        ctk.CTkButton(
            bottom_frame,
            text="Back",
            width=100,
            fg_color="#131112",
            hover_color="#ff4d94",
            text_color="white",
            command=self.go_back
        ).pack(side="left", padx=6, pady=6)

    def show_about(self):
        messagebox.showinfo("About", "Audio Steganography Tool")

    def clear_fields(self):
        self.message_box.delete("0.0", ctk.END)
        self.password_entry.delete(0, ctk.END)
        self.selected_wav_path = None
        self.output_wav_path = None
        self.selected_path_label.configure(text="No file selected")
        self.output_path_label.configure(text="Output: -")
        self.set_status("Ready", "neutral")

    def toggle_password(self):
        if self.password_entry.cget("show") == "":
            self.password_entry.configure(show="*")
            self.show_pw_btn.configure(text="Show")
        else:
            self.password_entry.configure(show="")
            self.show_pw_btn.configure(text="Hide")

    def set_status(self, message: str, status_type: str = "neutral"):
        color_map = {
            "success": "#ff1493",
            "warning": "#cc6699",
            "error": "#ff1a75",
            "neutral": "#cc6699"
        }
        self.status_label.configure(
            text=f"Status: {message}",
            text_color=color_map.get(status_type, "#cc6699")
        )

    def select_wav(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV audio files", "*.wav")])
        if file_path:
            self.selected_wav_path = file_path
            short = file_path if len(file_path) <= 80 else "..." + file_path[-77:]
            self.selected_path_label.configure(text=f"Selected: {short}")
            try:
                capacity = calculate_capacity_bytes(file_path)
                self.set_status(f"Selected. Capacity: {capacity} bytes", "neutral")
            except Exception:
                self.set_status("WAV file selected", "neutral")

    def on_hide_clicked(self):
        if not self.selected_wav_path:
            self.set_status("No WAV file selected", "error")
            return

        message = self.message_box.get("1.0", ctk.END).strip()
        password = self.password_entry.get().strip()

        if not message:
            self.set_status("Message is empty", "error")
            return
        if not password:
            self.set_status("Password is required", "error")
            return

        suggested = os.path.splitext(self.selected_wav_path)[0] + "_steg.wav"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            initialfile=os.path.basename(suggested),
            filetypes=[("WAV audio files", "*.wav")]
        )

        if not out_path:
            self.set_status("Save cancelled", "warning")
            return

        thread = threading.Thread(
            target=self._hide_task,
            args=(message, password, out_path),
            daemon=True
        )
        thread.start()

    def _hide_task(self, message: str, password: str, output_path: str):
        try:
            self.ui(self.set_status, "Encrypting message...", "neutral")
            encrypted_bytes, salt = encrypt_message(password, message)

            payload_len = len(encrypted_bytes)
            header = struct.pack(HEADER_FMT, MAGIC, salt, payload_len)
            payload = header + encrypted_bytes

            capacity_bytes = calculate_capacity_bytes(self.selected_wav_path)
            if len(payload) > capacity_bytes:
                self.ui(self.set_status, "Message too large for selected audio", "error")
                self.ui(messagebox.showerror, "Error", "Message too large for selected audio")
                return

            self.ui(self.set_status, "Hiding data into audio...", "neutral")
            hide_bytes_in_wav(
                self.selected_wav_path,
                output_path,
                payload,
                progress_callback=self._update_progress
            )

            self.output_wav_path = output_path
            short = output_path if len(output_path) <= 90 else "..." + output_path[-87:]
            self.ui(self.output_path_label.configure, text=f"Output: {short}")
            self.ui(self.set_status, "Message encrypted successfully", "success")
            self.ui(messagebox.showinfo, "Success", "Message encrypted successfully")

        except Exception as exc:
            self.ui(self.set_status, f"Error: {exc}", "error")
            self.ui(messagebox.showerror, "Error", str(exc))

    def _update_progress(self, fraction):
        pct = int(fraction * 100)
        self.ui(self.set_status, f"Working... {pct}%", "neutral")

    def on_extract_clicked(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV audio files", "*.wav")])
        if not file_path:
            self.set_status("Extraction cancelled", "warning")
            return

        password = self.password_entry.get().strip()
        if not password:
            self.set_status("Enter password to decrypt", "error")
            return

        self.selected_wav_path = file_path
        short = file_path if len(file_path) <= 80 else "..." + file_path[-77:]
        self.selected_path_label.configure(text=f"Selected: {short}")

        thread = threading.Thread(
            target=self._extract_task,
            args=(file_path, password),
            daemon=True
        )
        thread.start()

    def _extract_task(self, file_path: str, password: str):
        try:
            self.ui(self.set_status, "Extracting hidden data...", "neutral")
            salt, encrypted_bytes = extract_bytes_from_wav(
                file_path,
                progress_callback=self._update_progress
            )

            self.ui(self.set_status, "Decrypting message...", "neutral")
            try:
                message = decrypt_message(password, encrypted_bytes, salt)
            except Exception as e:
                raise ValueError("Decryption failed: wrong password or corrupted data.") from e

            self.ui(self.message_box.delete, "0.0", ctk.END)
            self.ui(self.message_box.insert, "0.0", message)
            self.ui(self.set_status, "Message decrypted successfully", "success")
            self.ui(messagebox.showinfo, "Success", "Message decrypted successfully")

        except Exception as exc:
            self.ui(self.set_status, f"Error: {exc}", "error")
            self.ui(messagebox.showerror, "Error", str(exc))


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Hidden Notes & Voice")
    root.geometry("1100x700")

    app = AudioStegApp(root)
    app.pack(fill="both", expand=True)

    root.mainloop()