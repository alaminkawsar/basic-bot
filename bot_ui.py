import tkinter as tk
from tkinter import filedialog, messagebox, Canvas
import datetime
import json
import os
import time

class ChatBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI File ChatBot")
        self.root.geometry("750x850")
        self.root.configure(bg="#ECECEC")

        # Files
        self.file1 = None
        self.file2 = None

        # Chat canvas + scrollbar (modern style)
        self.canvas = Canvas(root, bg="#ECECEC", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(root, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.chat_frame = tk.Frame(self.canvas, bg="#ECECEC")
        self.canvas.create_window((0, 0), window=self.chat_frame, anchor='nw')
        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # File button frame
        file_frame = tk.Frame(root, bg="#ECECEC")
        file_frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        tk.Button(file_frame, text="📂 Upload File 1", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), command=self.upload_file1).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="📂 Upload File 2", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), command=self.upload_file2).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="⚖ Compare Files", bg="#28A745", fg="white",
                  font=("Arial", 10, "bold"), command=self.compare_files).pack(side=tk.RIGHT, padx=5)

        # Input frame
        input_frame = tk.Frame(root, bg="#ECECEC")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.input_box = tk.Entry(input_frame, font=("Arial", 13))
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self.send_message)

        tk.Button(input_frame, text="Send", bg="#0078D7", fg="white",
                  font=("Arial", 11, "bold"), command=self.send_message).pack(side=tk.RIGHT)

        # Chat history
        self.history_file = "chat_history.json"
        self.load_history()

        if not self.chat_frame.winfo_children():
            self.add_message("Bot", "👋 Hello! I'm your AI File Assistant.\nYou can upload and compare files easily here.")

    # ---------------- Chat UI ----------------
    def add_message(self, sender, text):
        """Add message bubble to the chat."""
        frame = tk.Frame(self.chat_frame, bg="#ECECEC", pady=5)
        frame.pack(anchor="e" if sender == "You" else "w", fill="x", padx=10)

        color = "#DCF8C6" if sender == "You" else "#FFFFFF"
        anchor = "e" if sender == "You" else "w"

        msg_frame = tk.Frame(frame, bg=color, padx=10, pady=6)
        msg_frame.pack(anchor=anchor, padx=5, pady=2)

        tk.Label(msg_frame, text=text, bg=color, fg="black", wraplength=500,
                 justify="left", font=("Arial", 11)).pack(anchor=anchor)

        timestamp = datetime.datetime.now().strftime("%H:%M")
        tk.Label(frame, text=f"{sender} • {timestamp}", bg="#ECECEC", fg="#777", font=("Arial", 8)).pack(anchor=anchor)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)
        self.save_message(sender, text)

    def send_message(self, event=None):
        text = self.input_box.get().strip()
        if not text:
            return
        self.add_message("You", text)
        self.input_box.delete(0, tk.END)
        self.root.after(400, lambda: self.respond(text))

    def respond(self, user_text):
        """Generate simple smart responses."""
        text = user_text.lower()
        if "hello" in text or "hi" in text:
            reply = "Hi there! 😊 Upload your files to get started."
        elif "compare" in text:
            reply = "You can compare two uploaded files by clicking '⚖ Compare Files'."
        elif "file" in text:
            reply = "Try uploading files using the buttons above. I can show details and compare them."
        elif "thank" in text:
            reply = "You're welcome! 💬"
        elif "help" in text:
            reply = "Sure! You can:\n1️⃣ Upload files\n2️⃣ Compare two files\n3️⃣ Ask me to show file info"
        elif "info" in text or "detail" in text:
            reply = self.get_file_info()
        else:
            reply = "I'm still learning 🤖 but I can handle files and comparisons."
        self.add_message("Bot", reply)

    # ---------------- File Upload ----------------
    def upload_file1(self):
        path = filedialog.askopenfilename(title="Select File 1")
        if path:
            self.file1 = path
            self.show_file_info(1, path)

    def upload_file2(self):
        path = filedialog.askopenfilename(title="Select File 2")
        if path:
            self.file2 = path
            self.show_file_info(2, path)

    def show_file_info(self, file_num, path):
        """Display basic file info in chat."""
        size = os.path.getsize(path)
        modified = time.ctime(os.path.getmtime(path))
        name = os.path.basename(path)
        ext = os.path.splitext(path)[1]
        info = f"📄 File {file_num} uploaded:\n• Name: {name}\n• Type: {ext}\n• Size: {size/1024:.2f} KB\n• Modified: {modified}"
        self.add_message("Bot", info)

    def get_file_info(self):
        """Return info of uploaded files."""
        if not self.file1 and not self.file2:
            return "No files uploaded yet. 📁"
        info = ""
        if self.file1:
            info += f"File 1: {os.path.basename(self.file1)}\n"
        if self.file2:
            info += f"File 2: {os.path.basename(self.file2)}"
        return info or "No files found."

    # ---------------- File Comparison ----------------
    def compare_files(self):
        if not self.file1 or not self.file2:
            messagebox.showwarning("Missing Files", "Please upload both files before comparing.")
            return

        try:
            with open(self.file1, "r", encoding="utf-8", errors="ignore") as f1, \
                 open(self.file2, "r", encoding="utf-8", errors="ignore") as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()

            differences = []
            for i, (l1, l2) in enumerate(zip(lines1, lines2), start=1):
                if l1.strip() != l2.strip():
                    differences.append(f"Line {i}:\n🔹 {l1.strip()}\n🔸 {l2.strip()}")

            if len(lines1) != len(lines2):
                differences.append(f"⚠ Files have different line counts ({len(lines1)} vs {len(lines2)}).")

            if differences:
                diff_text = "\n\n".join(differences[:10])  # Show only first 10 differences
                self.add_message("Bot", f"Found differences:\n{diff_text}")
            else:
                self.add_message("Bot", "✅ The files are identical!")
        except Exception as e:
            self.add_message("Bot", f"❌ Error comparing files: {e}")

    # ---------------- History ----------------
    def save_message(self, sender, text):
        history = self.load_history_data()
        history.append({
            "sender": sender,
            "message": text,
            "time": str(datetime.datetime.now())
        })
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

    def load_history_data(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def load_history(self):
        history = self.load_history_data()
        for msg in history:
            self.add_message(msg["sender"], msg["message"])


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatBotApp(root)
    root.mainloop()
