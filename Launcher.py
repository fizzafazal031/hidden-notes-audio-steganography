import customtkinter as ctk
from notes_app import SecureNotesApp
from audio_app import AudioStegApp

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hidden Notes & Voice")
        self.geometry("900x600")
        self.resizable(False, False)

        self.current_frame = None
        self.show_home()

    def clear_current_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def show_home(self):
        self.clear_current_frame()
        self.current_frame = HomePage(self)
        self.current_frame.pack(fill="both", expand=True)

    def open_notes(self):
        self.clear_current_frame()
        self.current_frame = SecureNotesApp(self, back_callback=self.show_home)
        self.current_frame.pack(fill="both", expand=True)

    def open_audio(self):
        self.clear_current_frame()
        self.current_frame = AudioStegApp(self, back_callback=self.show_home)
        self.current_frame.pack(fill="both", expand=True)


class HomePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#ffe6f0")

        ctk.CTkLabel(
            self,
            text="Choose What You Want",
            font=("Arial", 24, "bold")
        ).pack(pady=(80, 30))

        ctk.CTkButton(
            self,
            text="Open Hidden Notes",
            command=master.open_notes,
            width=220,
            height=45,
            corner_radius=12,
            fg_color="#ff69b4",
            font=("Arial", 14, "bold")
        ).pack(pady=15)

        ctk.CTkButton(
            self,
            text="Open Hidden Voice",
            command=master.open_audio,
            width=220,
            height=45,
            corner_radius=12,
            fg_color="#ff69b4",
            font=("Arial", 14, "bold")
        ).pack(pady=15)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()