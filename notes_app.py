import json
import os
import hashlib
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import customtkinter as ctk
from tkinter import messagebox

DATA_FILE = "notes.json"
BLOCK_SIZE = 16


def derive_key(master_password: str) -> bytes:
    return hashlib.sha256(master_password.encode()).digest()


def encrypt_text(text: str, key: bytes) -> str:
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(text.encode("utf-8"), BLOCK_SIZE))
    iv = base64.b64encode(cipher.iv).decode("utf-8")
    ct = base64.b64encode(ct_bytes).decode("utf-8")
    return json.dumps({"iv": iv, "ciphertext": ct})


def decrypt_text(enc_json: str, key: bytes):
    try:
        data = json.loads(enc_json)
        iv = base64.b64decode(data["iv"])
        ct = base64.b64decode(data["ciphertext"])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), BLOCK_SIZE)
        return pt.decode("utf-8")
    except Exception:
        return None


def load_notes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_notes(notes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=4)


class SecureNotesApp(ctk.CTkFrame):
    def __init__(self, master, back_callback=None):
        super().__init__(master, fg_color="#ffe6f0")
        self.back_callback = back_callback

        self.master_password = ""
        self.key = None
        self.notes = {}
        self.search_var = ctk.StringVar()

        self.count_label = None
        self.pass_entry = None

        self.show_login_frame()

    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

    def go_back(self):
        if self.back_callback:
            self.back_callback()

    def make_popup_stable(self, popup):
        popup.lift()
        popup.attributes("-topmost", True)
        popup.after(200, lambda: popup.attributes("-topmost", False))
        popup.focus_force()
        popup.grab_set()

    def show_login_frame(self):
        self.clear_frame()

        login_frame = ctk.CTkFrame(self, fg_color="#ffd6eb")
        login_frame.pack(pady=50, padx=50, fill="both", expand=True)

        ctk.CTkLabel(
            login_frame,
            text="Secure Notes Login",
            font=("Arial", 22, "bold"),
            text_color="#660033"
        ).pack(pady=(50, 20))

        self.pass_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Enter Master Password",
            show="*",
            width=300,
            height=45,
            corner_radius=10,
            fg_color="#fff0f5",
            text_color="#660033",
            placeholder_text_color="#aa6688",
            font=("Arial", 14, "bold")
        )
        self.pass_entry.pack(pady=20)

        ctk.CTkButton(
            login_frame,
            text="Login",
            command=self.login,
            width=220,
            height=45,
            corner_radius=15,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        bottom_bar = ctk.CTkFrame(login_frame, fg_color="#ffe6f0")
        bottom_bar.pack(fill="x", side="bottom", padx=10, pady=10)

        ctk.CTkButton(
            bottom_bar,
            text=" Back",
            command=self.go_back,
            width=100,
            fg_color="#131112",
            hover_color="#ff4d94",
            text_color="white",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=8)

    def login(self):
        password = self.pass_entry.get().strip()
        if not password:
            messagebox.showwarning("Warning", "Enter Master Password")
            return

        self.master_password = password
        self.key = derive_key(password)
        self.notes = load_notes()
        self.show_notes_frame()

    def show_notes_frame(self):
        self.clear_frame()

        notes_frame = ctk.CTkFrame(self, fg_color="#ffe6f0")
        notes_frame.pack(pady=20, padx=20, fill="both", expand=True)

        top_bar = ctk.CTkFrame(notes_frame, fg_color="#ffd6eb")
        top_bar.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(
            top_bar,
            text="Secure Notes",
            font=("Arial", 20, "bold"),
            text_color="#660033"
        ).pack(side="left", padx=20, pady=10)

        search_frame = ctk.CTkFrame(notes_frame, fg_color="#ffd6eb")
        search_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(
            search_frame,
            text="Search:",
            font=("Arial", 14, "bold"),
            text_color="#660033"
        ).pack(side="left", padx=10)

        ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=250,
            height=35,
            corner_radius=8,
            fg_color="#fff0f5",
            text_color="#660033",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            search_frame,
            text="Filter",
            command=self.view_notes_popup,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=90,
            height=35,
            corner_radius=8,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(notes_frame, fg_color="#ffd6eb")
        btn_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Add Note",
            command=self.add_note_popup,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=120,
            height=40,
            corner_radius=12,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="View Notes",
            command=self.view_notes_popup,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=120,
            height=40,
            corner_radius=12,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Delete Note",
            command=self.delete_note_popup,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=120,
            height=40,
            corner_radius=12,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=10)

        self.count_label = ctk.CTkLabel(
            notes_frame,
            text=f"Total Notes: {len(self.notes)}",
            font=("Arial", 14, "bold"),
            text_color="#660033"
        )
        self.count_label.pack(pady=10)

        bottom_bar = ctk.CTkFrame(notes_frame, fg_color="#ffd6eb")
        bottom_bar.pack(fill="x", side="bottom", padx=10, pady=10)

        ctk.CTkButton(
            bottom_bar,
            text="Back",
            command=self.go_back,
            width=100,
            fg_color="#131112",
            hover_color="#ff4d94",
            text_color="white",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=8)

    def add_note_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.geometry("450x400")
        popup.title("Add Note")
        popup.configure(fg_color="#ffe6f0")
        self.make_popup_stable(popup)

        ctk.CTkLabel(
            popup,
            text="Add New Note",
            font=("Arial", 18, "bold"),
            text_color="#660033"
        ).pack(pady=10)

        title_entry = ctk.CTkEntry(
            popup,
            placeholder_text="Title",
            width=350,
            height=40,
            corner_radius=10,
            fg_color="#fff0f5",
            text_color="#660033",
            placeholder_text_color="#aa6688",
            font=("Arial", 14, "bold")
        )
        title_entry.pack(pady=15)

        content_entry = ctk.CTkTextbox(
            popup,
            height=220,
            font=("Arial", 12, "bold"),
            fg_color="#fff0f5",
            text_color="#660033"
        )
        content_entry.pack(pady=10, padx=10, fill="both", expand=True)

        def save():
            title = title_entry.get().strip()
            content = content_entry.get("1.0", "end-1c").strip()

            if not title or not content:
                messagebox.showwarning("Warning", "Title and content cannot be empty")
                return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enc_content = encrypt_text(content, self.key)
            self.notes[title] = {"content": enc_content, "timestamp": timestamp}
            save_notes(self.notes)

            if self.count_label:
                self.count_label.configure(text=f"Total Notes: {len(self.notes)}")

            messagebox.showinfo("Success", "Note added successfully")
            popup.destroy()

        ctk.CTkButton(
            popup,
            text="Save",
            command=save,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=160,
            height=45,
            corner_radius=15,
            font=("Arial", 14, "bold")
        ).pack(pady=5)

    def view_notes_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.geometry("650x500")
        popup.title("View Notes")
        popup.configure(fg_color="#ffe6f0")
        self.make_popup_stable(popup)

        filter_text = self.search_var.get().lower().strip()

        scroll = ctk.CTkScrollableFrame(popup, fg_color="#ffe6f0")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        found = False
        for title, data in self.notes.items():
            if filter_text and filter_text not in title.lower():
                continue

            found = True
            content = decrypt_text(data["content"], self.key)
            if content is None:
                content = "[Decryption Failed]"

            timestamp = data.get("timestamp", "")

            note_frame = ctk.CTkFrame(scroll, fg_color="#ffd6eb", corner_radius=10)
            note_frame.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(
                note_frame,
                text=f"Title: {title}",
                font=("Arial", 14, "bold"),
                text_color="#660033"
            ).pack(anchor="w", padx=8, pady=(8, 2))

            ctk.CTkLabel(
                note_frame,
                text=f"Content: {content}",
                wraplength=580,
                justify="left",
                font=("Arial", 12, "bold"),
                text_color="#660033"
            ).pack(anchor="w", padx=8, pady=2)

            ctk.CTkLabel(
                note_frame,
                text=f"Added: {timestamp}",
                font=("Arial", 12, "italic"),
                text_color="#994d73"
            ).pack(anchor="w", padx=8, pady=(2, 8))

        if not found:
            ctk.CTkLabel(
                scroll,
                text="No notes found",
                font=("Arial", 14, "bold"),
                text_color="#660033"
            ).pack(pady=20)

    def delete_note_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.geometry("400x300")
        popup.title("Delete Note")
        popup.configure(fg_color="#ffe6f0")
        self.make_popup_stable(popup)

        ctk.CTkLabel(
            popup,
            text="Delete Note",
            font=("Arial", 18, "bold"),
            text_color="#660033"
        ).pack(pady=15)

        title_entry = ctk.CTkEntry(
            popup,
            placeholder_text="Title to Delete",
            width=300,
            height=40,
            corner_radius=10,
            fg_color="#fff0f5",
            text_color="#660033",
            placeholder_text_color="#aa6688",
            font=("Arial", 14, "bold")
        )
        title_entry.pack(pady=10)

        password_entry = ctk.CTkEntry(
            popup,
            placeholder_text="Enter Original Note Password",
            show="*",
            width=300,
            height=40,
            corner_radius=10,
            fg_color="#fff0f5",
            text_color="#660033",
            placeholder_text_color="#aa6688",
            font=("Arial", 14, "bold")
        )
        password_entry.pack(pady=10)


        def delete():
            title = title_entry.get().strip()
            entered_password = password_entry.get().strip()

            if not title:
                messagebox.showwarning("Warning", "Enter note title")
                return

            if not entered_password:
                messagebox.showwarning("Warning", "Enter password")
                return

            if title not in self.notes:
                messagebox.showwarning("Warning", f"No note with title '{title}' found")
                return

            entered_key = derive_key(entered_password)
            encrypted_content = self.notes[title]["content"]
            decrypted_content = decrypt_text(encrypted_content, entered_key)

            if decrypted_content is None:
                messagebox.showerror(
                    "Error",
                    "Incorrect password."
                )
                return

            del self.notes[title]
            save_notes(self.notes)

            if self.count_label:
                self.count_label.configure(text=f"Total Notes: {len(self.notes)}")

            messagebox.showinfo("Success", f"Note '{title}' deleted successfully")
            popup.destroy()

        ctk.CTkButton(
            popup,
            text="Delete",
            command=delete,
            fg_color="#ff69b4",
            hover_color="#ff4d94",
            text_color="white",
            width=160,
            height=45,
            corner_radius=15,
            font=("Arial", 14, "bold")
        ).pack(pady=15)


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.geometry("900x650")
    root.title("Secure Notes")

    app = SecureNotesApp(root)
    app.pack(fill="both", expand=True, padx=10, pady=10)

    root.mainloop()