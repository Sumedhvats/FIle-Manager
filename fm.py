import os
import sys
import platform
import subprocess
from os import listdir, remove, makedirs
from os.path import join, exists, splitext, expanduser, dirname, abspath
from shutil import move, copy2
from tkinter import filedialog, messagebox, Tk, Listbox, Button, Scrollbar, Label, Text, Frame, PhotoImage, StringVar, END, BOTH, LEFT, RIGHT, Y, X, TOP, BOTTOM, SUNKEN
from tkinter import font as tkfont
from tkinter import simpledialog, ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ========================
# Cross-Platform Configuration
# ========================

def resource_path(relative_path):
    """ Get absolute path to resources for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")
    return join(base_path, relative_path)

# Supported file extensions
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
VIDEO_EXTENSIONS = [".webm", ".mpg", ".mp4", ".avi", ".mkv"]
AUDIO_EXTENSIONS = [".m4a", ".mp3", ".wav"]
DOCUMENT_EXTENSIONS = [".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]

class MoverHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_event(event)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.handle_event(event)

    def handle_event(self, event):
        self.app.refresh_file_list()
        with os.scandir(self.app.source_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    self.app.auto_move_file(entry.path)

class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FileFlow: Cross-Platform File Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2c3e50")  # Dark background

        # Modern color scheme
        self.colors = {
            "background": "#2c3e50",
            "secondary_bg": "#34495e",
            "text": "#ecf0f1",
            "accent": "#3498db",
            "hover": "#2980b9"
        }

        # Custom font
        self.font_styles = {
            "main": ("Segoe UI", 10),
            "title": ("Segoe UI", 12, "bold"),
            "log": ("Consolas", 10)
        }

        self.clipboard_file = None
        self.clipboard_action = None
        self.auto_move_enabled = True
        
        # Home directory file management folder
        self.source_dir = join(expanduser("~"), "Downloads", "ewFile")

        # Destination directories
        self.dest_dirs = {
            'image': join(self.source_dir, "image"),
            'video': join(self.source_dir, "video"),
            'music': join(self.source_dir, "music"),
            'documents': join(self.source_dir, "document")
        }

        self.create_directories()
        self.create_ui()
        self.start_observer()

    def create_directories(self):
        # Create required directories
        directories = [self.source_dir] + list(self.dest_dirs.values())
        for directory in directories:
            makedirs(directory, exist_ok=True)

    def create_ui(self):
        # Main container
        main_frame = Frame(self.root, bg=self.colors["background"])
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Path display
        self.path_var = StringVar(value=self.source_dir)
        path_label = Label(
            main_frame, 
            textvariable=self.path_var, 
            bg=self.colors["secondary_bg"], 
            fg=self.colors["text"],
            font=self.font_styles["main"],
            relief=SUNKEN,
            anchor='w',
            padx=10
        )
        path_label.pack(fill=X, pady=(0, 5))

        # File List Frame with Modern Treeview
        list_frame = Frame(main_frame, bg=self.colors["background"])
        list_frame.pack(fill=BOTH, expand=True)

        # Treeview for file list
        self.file_tree = ttk.Treeview(
            list_frame, 
            columns=("Name", "Type", "Size"), 
            show="headings"
        )
        self.file_tree.heading("Name", text="Name", anchor='w')
        self.file_tree.heading("Type", text="Type", anchor='w')
        self.file_tree.heading("Size", text="Size", anchor='e')
        
        self.file_tree.column("Name", width=400, stretch=True)
        self.file_tree.column("Type", width=100)
        self.file_tree.column("Size", width=100, anchor='e')
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscroll=scrollbar.set)

        self.file_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Bind double-click to open
        self.file_tree.bind("<Double-1>", self.open_item)

        # Toolbar with improved styling
        toolbar = Frame(main_frame, bg=self.colors["secondary_bg"])
        toolbar.pack(fill=X, pady=(5, 0))

        # Toolbar buttons with text and icons
        toolbar_buttons = [
            ("Cut", self.cut_selected_file),
            ("Copy", self.copy_selected_file),
            ("Paste", self.paste_file),
            ("Delete", self.delete_selected_file),
            ("Back", self.go_back),
            ("New Folder", self.add_subfolder)
        ]

        for text, command in toolbar_buttons:
            btn = self.create_toolbar_button(toolbar, text, command)
            btn.pack(side=LEFT, padx=5, pady=5)

        # Log area with console-like styling
        log_frame = Frame(main_frame, bg=self.colors["secondary_bg"])
        log_frame.pack(fill=X, pady=(5, 0))

        self.log_text = Text(
            log_frame, 
            height=6, 
            bg="#000000", 
            fg="#00ff00", 
            font=self.font_styles["log"]
        )
        self.log_text.pack(fill=X, padx=5, pady=5)

        # Refresh file list on startup
        self.refresh_file_list()

    def create_toolbar_button(self, parent, text, command):
        # Create a modern, styled toolbar button
        btn = Button(
            parent, 
            text=text, 
            command=command,
            bg=self.colors["accent"],
            fg=self.colors["text"],
            font=self.font_styles["main"],
            activebackground=self.colors["hover"],
            relief='flat'
        )
        return btn

    def log_action(self, action):
        self.log_text.insert(END, f"{action}\n")
        self.log_text.see(END)

    def auto_move_file(self, entry):
        if not self.auto_move_enabled:
            return

        filename = os.path.basename(entry)
        ext = splitext(filename)[1].lower()

        # Skip if already in one of the destination folders
        if os.path.dirname(entry) in list(self.dest_dirs.values()):
            self.log_action(f"Skipped auto-moving '{filename}' (already sorted)")
            return

        if os.path.dirname(entry) == self.source_dir:
            try:
                if ext in IMAGE_EXTENSIONS:
                    self.move_file(entry, self.dest_dirs['image'])
                elif ext in VIDEO_EXTENSIONS:
                    self.move_file(entry, self.dest_dirs['video'])
                elif ext in AUDIO_EXTENSIONS:
                    self.move_file(entry, self.dest_dirs['music'])
                elif ext in DOCUMENT_EXTENSIONS:
                    self.move_file(entry, self.dest_dirs['documents'])
                else:
                    self.log_action(f"Unsupported file type: {filename}")
            except Exception as e:
                self.log_action(f"Auto-move error: {e}")

    def move_file(self, src_path, dest_dir):
        try:
            filename = os.path.basename(src_path)
            dest_path = join(dest_dir, filename)
            move(src_path, dest_path)
            self.log_action(f"Moved '{filename}' to '{os.path.basename(dest_dir)}'")
            self.refresh_file_list()
        except Exception as e:
            self.log_action(f"Error moving file: {e}")

    def copy_file(self, src_path, dest_dir):
        try:
            filename = os.path.basename(src_path)
            dest_path = join(dest_dir, filename)
            copy2(src_path, dest_path)
            self.log_action(f"Copied '{filename}' to '{os.path.basename(dest_dir)}'")
        except Exception as e:
            self.log_action(f"Error copying file: {e}")

    def refresh_file_list(self):
        # Clear existing items
        for i in self.file_tree.get_children():
            self.file_tree.delete(i)

        try:
            with os.scandir(self.source_dir) as entries:
                for entry in entries:
                    try:
                        # Get file details
                        file_type = "Folder" if entry.is_dir() else splitext(entry.name)[1][1:].upper() + " File"
                        file_size = f"{entry.stat().st_size / 1024:.1f} KB" if entry.is_file() else "-"
                        
                        # Insert into treeview
                        self.file_tree.insert("", "end", values=(
                            entry.name, 
                            file_type, 
                            file_size
                        ))
                    except Exception as e:
                        print(f"Error processing {entry.name}: {e}")

            self.path_var.set(f"Current Path: {self.source_dir}")
            self.log_action("File list refreshed.")
        except Exception as e:
            self.log_action(f"Error refreshing file list: {e}")

    def cut_selected_file(self):
        try:
            selected_item = self.file_tree.selection()[0]
            selected_file = self.file_tree.item(selected_item)['values'][0]
            self.clipboard_file = join(self.source_dir, selected_file)
            self.clipboard_action = "cut"
            self.log_action(f"Cut selected: {selected_file}")
        except IndexError:
            self.log_action("No file selected")

    def copy_selected_file(self):
        try:
            selected_item = self.file_tree.selection()[0]
            selected_file = self.file_tree.item(selected_item)['values'][0]
            self.clipboard_file = join(self.source_dir, selected_file)
            self.clipboard_action = "copy"
            self.log_action(f"Copied selected: {selected_file}")
        except IndexError:
            self.log_action("No file selected")

    def paste_file(self):
        if self.clipboard_file and self.clipboard_action:
            try:
                self.auto_move_enabled = False
                filename = os.path.basename(self.clipboard_file)
                dest_path = join(self.source_dir, filename)

                if exists(dest_path):
                    self.log_action(f"File exists: {filename}")
                    return

                if self.clipboard_action == "cut":
                    move(self.clipboard_file, dest_path)
                    self.log_action(f"Moved '{filename}' to current folder")
                elif self.clipboard_action == "copy":
                    copy2(self.clipboard_file, dest_path)
                    self.log_action(f"Copied '{filename}' to current folder")

                self.clipboard_file = None
                self.clipboard_action = None
                self.refresh_file_list()
            except Exception as e:
                self.log_action(f"Paste error: {e}")
            finally:
                self.auto_move_enabled = True
        else:
            self.log_action("No file to paste")

    def delete_selected_file(self):
        try:
            selected_item = self.file_tree.selection()[0]
            selected_file = self.file_tree.item(selected_item)['values'][0]
            file_path = join(self.source_dir, selected_file)
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {selected_file}?"):
                remove(file_path)
                self.log_action(f"Deleted: {selected_file}")
                self.refresh_file_list()
        except IndexError:
            self.log_action("No file selected")
        except Exception as e:
            self.log_action(f"Delete error: {e}")

    def open_item(self, event):
        try:
            selected_item = self.file_tree.selection()[0]
            selected_file = self.file_tree.item(selected_item)['values'][0]
            file_path = join(self.source_dir, selected_file)
            
            if os.path.isdir(file_path):
                self.source_dir = file_path
                self.refresh_file_list()
                self.log_action(f"Opened: {selected_file}")
            elif os.path.isfile(file_path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    else:
                        subprocess.run(['xdg-open', file_path])
                    self.log_action(f"Opened: {selected_file}")
                except Exception as e:
                    self.log_action(f"Open error: {e}")
        except IndexError:
            self.log_action("No item selected")

    def go_back(self):
        parent_dir = dirname(self.source_dir)
        if parent_dir and exists(parent_dir):
            self.source_dir = parent_dir
            self.refresh_file_list()
            self.log_action(f"Back to: {parent_dir}")

    def add_subfolder(self):
        new_folder = simpledialog.askstring("New Folder", "Folder name:")
        if new_folder:
            new_path = join(self.source_dir, new_folder)
            if not exists(new_path):
                makedirs(new_path)
                self.log_action(f"Created: {new_folder}")
                self.refresh_file_list()
            else:
                self.log_action(f"Folder already exists: {new_folder}")

    def start_observer(self):
        event_handler = MoverHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.source_dir, recursive=True)
        observer.daemon = True  # Allow the thread to exit when the main program exits
        observer.start()

def main():
    root = Tk()
    app = FileManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()