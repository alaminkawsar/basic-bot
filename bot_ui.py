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
        self.root.geometry("780x900")
        self.root.configure(bg="#ECECEC")

        # Files
        self.file1 = None
        self.file2 = None

        # Chat canvas with scrollbar
        self.canvas = Canvas(root, bg="#ECECEC", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(root, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.chat_frame = tk.Frame(self.canvas, bg="#ECECEC")
        # create window and keep its id so we can resize it when the main canvas size changes
        self.window_id = self.canvas.create_window((0, 0), window=self.chat_frame, anchor='nw', width=self.canvas.winfo_width())
        # update scrollregion when chat_frame changes
        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # ensure chat_frame width follows canvas width (dynamic resizing)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # File button frame
        file_frame = tk.Frame(root, bg="#ECECEC")
        file_frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        tk.Button(file_frame, text="📂 Upload File 1", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), command=self.upload_file1).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="📂 Upload File 2", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), command=self.upload_file2).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="⚖ Compare Files", bg="#28A745", fg="white",
                  font=("Arial", 10, "bold"), command=self.compare_files).pack(side=tk.RIGHT, padx=5)

        # Input frame (larger text field) - made responsive and "pill" styled
        input_container = tk.Frame(root, bg="#ECECEC")
        input_container.pack(fill=tk.X, padx=10, pady=10)

        # We use a canvas to draw a rounded background (pill) and place the Text on top so it visually looks rounded.
        self.input_bg = tk.Canvas(input_container, height=56, bg="#ECECEC", highlightthickness=0)
        self.input_bg.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 8))

        # Draw rounded rect as input background; we'll redraw on resize
        self._draw_input_bg()

        # Text widget for multi-line input. We make it borderless so it appears inside the rounded bg.
        self.input_box = tk.Text(self.input_bg, height=2, font=("Arial", 13), wrap=tk.WORD,
                                 bg="#F6F6F6", bd=0, padx=10, pady=8, relief="flat")
        # put text widget into the canvas
        self.input_window = self.input_bg.create_window(12, 8, window=self.input_box, anchor='nw', width=self._input_text_width())
        self.input_box.bind("<Return>", self.send_message)
        self.input_box.bind("<Shift-Return>", lambda e: self.input_box.insert(tk.INSERT, "\n"))

        # Custom rounded send button (canvas based for pill/rounded look)
        self.send_btn_canvas = tk.Canvas(input_container, width=80, height=56, bg="#ECECEC", highlightthickness=0)
        self.send_btn_canvas.pack(side=tk.RIGHT)
        self._draw_send_button()
        # bind send action to the send button canvas (both click and Enter key)
        self.send_btn_canvas.tag_bind("send_btn", "<Button-1>", lambda e: self.send_message())
        self.send_btn_canvas.tag_bind("send_btn", "<Enter>", lambda e: self.send_btn_canvas.config(cursor="hand2"))

        # ensure elements adjust when window resizes
        root.bind("<Configure>", self._on_root_configure)

        # Chat history
        self.history_file = "chat_history.json"
        self.load_history()

        if not self.chat_frame.winfo_children():
            self.add_message("Bot", "👋 Hello! I'm your AI File Assistant.\nYou can upload and compare files easily here.")

    # ---------------- Dynamic layout helpers ----------------
    def _on_canvas_configure(self, event):
        # make the chat_frame window follow the canvas width so messages wrap properly when resizing
        try:
            self.canvas.itemconfigure(self.window_id, width=event.width)
        except Exception:
            pass

    def _on_root_configure(self, event):
        # redraw input background and move input text window to the new width
        self._draw_input_bg()
        try:
            self.input_bg.coords(self.input_window, 12, 8)
            self.input_bg.itemconfigure(self.input_window, width=self._input_text_width())
        except Exception:
            pass
        # also redraw send button to center content if necessary
        self._draw_send_button()

    def _input_text_width(self):
        # compute available width for the Text inside the input_bg
        # subtract paddings and reserve space for send button
        total = self.input_bg.winfo_width()
        if not total or total < 100:
            # fallback default width
            return 560
        return max(80, total - 24)

    # ---------------- Rounded shapes ----------------
    def _rounded_rect(self, canvas, x1, y1, x2, y2, r=10, **kwargs):
        # Draw rounded rectangle by composing arcs and rectangles (approximated using a smooth polygon)
        return canvas.create_polygon(
            [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2 - r,
                x1, y1 + r
            ],
            smooth=True,
            splinesteps=12,
            **kwargs
        )

    def _draw_input_bg(self):
        self.input_bg.delete("all")
        w = self.input_bg.winfo_width() or max(200, self.root.winfo_width() - 140)
        h = 56
        pad = 2
        r = 28  # big radius for pill effect
        bg_fill = "#F6F6F6"
        self._rounded_rect(self.input_bg, pad, pad, max(w, 120) - pad, h - pad, r=r, fill=bg_fill, outline="#E0E0E0")

    def _draw_send_button(self):
        self.send_btn_canvas.delete("all")
        w = self.send_btn_canvas.winfo_width() or 80
        h = self.send_btn_canvas.winfo_height() or 56
        r = 14
        # draw rounded button background
        btn_id = self._rounded_rect(self.send_btn_canvas, 6, 6, w - 6, h - 6, r=r, fill="#0078D7", outline="#0062B0")
        # draw label inside
        self.send_btn_canvas.create_text(w / 2, h / 2, text="Send", fill="white", font=("Arial", 11, "bold"), tags=("send_btn",))
        # mark the rounded rect as clickable as well
        self.send_btn_canvas.addtag_withtag("send_btn", btn_id)

    # ---------------- Chat UI ----------------
    def add_message(self, sender, text):
        """Add message bubble with alignment and rounded bubble using a small canvas per message."""
        outer = tk.Frame(self.chat_frame, bg="#ECECEC", pady=5)
        outer.pack(fill="x", padx=10)

        # alignment and colors
        align = "e" if sender == "You" else "w"
        bubble_color = "#DCF8C6" if sender == "You" else "#FFFFFF"
        text_color = "#000000"

        # small canvas to paint rounded bubble and text
        bubble_canvas = tk.Canvas(outer, bg="#ECECEC", highlightthickness=0)
        # anchor it left or right
        bubble_canvas.pack(anchor=align)

        # decide max width relative to the main canvas (responsive)
        try:
            max_bubble_w = min(520, int(self.canvas.winfo_width() * 0.75))
            if max_bubble_w <= 0:
                max_bubble_w = 520
        except Exception:
            max_bubble_w = 520

        # create the text first (wrapped)
        text_id = bubble_canvas.create_text(12, 8, text=text, anchor="nw", font=("Arial", 11), fill=text_color, width=max_bubble_w)
        bubble_canvas.update_idletasks()
        bbox = bubble_canvas.bbox(text_id)  # (x1,y1,x2,y2)
        if not bbox:
            bbox = (0, 0, 10, 10)
        pad_x = 12
        pad_y = 8
        x1 = bbox[0] - pad_x
        y1 = bbox[1] - pad_y
        x2 = bbox[2] + pad_x
        y2 = bbox[3] + pad_y
        w = x2 - x1
        h = y2 - y1
        # configure canvas to actual size
        bubble_canvas.config(width=w, height=h)
        # move text into new coordinates (we created text at 12,8 so shifting to pad position)
        bubble_canvas.coords(text_id, pad_x, pad_y)

        # draw rounded bubble behind the text
        r = min(18, int(h / 2))
        rect_id = self._rounded_rect(bubble_canvas, 0, 0, w, h, r=r, fill=bubble_color, outline="#EDEDED")
        # ensure rectangle is behind text
        bubble_canvas.tag_lower(rect_id, text_id)

        # timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        meta = tk.Label(outer, text=f"{sender} • {timestamp}", bg="#ECECEC", fg="#777", font=("Arial", 8))
        meta.pack(anchor=align)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)
        self.save_message(sender, text)

    def send_message(self, event=None):
        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            # prevent newline on Enter when text is empty
            return "break"
        self.add_message("You", text)
        self.input_box.delete("1.0", tk.END)
        self.root.after(200, lambda: self.respond(text))
        return "break"

    def respond(self, user_text):
        """Generate smart responses."""
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
        size = os.path.getsize(path)
        modified = time.ctime(os.path.getmtime(path))
        name = os.path.basename(path)
        ext = os.path.splitext(path)[1]
        info = f"📄 File {file_num} uploaded:\n• Name: {name}\n• Type: {ext}\n• Size: {size/1024:.2f} KB\n• Modified: {modified}"
        self.add_message("Bot", info)

    def get_file_info(self):
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
                diff_text = "\n\n".join(differences[:10])
                self.add_message("Bot", f"Found differences:\n{diff_text}")
            else:
                self.add_message("Bot", "✅ The files are identical!")
        except Exception as e:
            self.add_message("Bot", f"❌ Error comparing files: {e}")

    # ---------------- History ----------------
    def save_message(self, sender, text):
        history = self.load_history_data()
        history.append({"sender": sender, "message": text, "time": str(datetime.datetime.now())})
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
