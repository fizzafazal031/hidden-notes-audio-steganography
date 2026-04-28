# hidden-notes-audio-steganography
A Python desktop application using CustomTkinter that provides secure note storage with AES encryption and audio steganography using WAV files to hide and extract secret messages with password-based encryption
Features

# 📝 Secure Notes
- Add, view, search, and delete notes
- All notes are protected using **AES encryption**
- Master password required to access notes

# 🎧 Audio Steganography
- Hide secret messages inside WAV audio files
- Extract hidden messages using password
- Uses LSB (Least Significant Bit) technique
- Extra security with **Fernet encryption**

# 🔐 Security Features
- Password-based encryption
- PBKDF2 key derivation
- Data cannot be read without correct password

  # 🛠️ Technologies Used
- Python
- CustomTkinter (GUI)
- Cryptography (AES, Fernet)
- hashlib & PBKDF2
- wave module (audio processing)
- struct, base64

# 🛠️ Libraries Used

🎨 GUI
- CustomTkinter: Modern and attractive user interface create karne ke liye

🔐 Security
- cryptography: Messages ko encrypt aur decrypt karne ke liye (AES/Fernet)
