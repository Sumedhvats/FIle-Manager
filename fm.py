import os
from os import listdir, remove, makedirs
from os.path import join, exists, splitext
from shutil import move, copy2
from tkinter import filedialog, messagebox, Tk, Listbox, Button, Scrollbar, Label, Text, Frame, PhotoImage, StringVar, END
from tkinter import font as tkfont
from tkinter import simpledialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define source and destination directories
source_dir = "C:/Users/SUMEDH/Downloads/ewFile"
dest_dir_image = "C:/Users/SUMEDH/Downloads/ewFile/image"
dest_dir_video = "C:/Users/SUMEDH/Downloads/ewFile/video"
dest_dir_music = "C:/Users/SUMEDH/Downloads/ewFile/music"
dest_dir_documents = "C:/Users/SUMEDH/Downloads/ewFile/document"

# Ensure all destination directories exist
for directory in [source_dir, dest_dir_image, dest_dir_video, dest_dir_music, dest_dir_documents]:
    if not exists(directory):
        os.makedirs(directory)

# Supported file extensions for sorting
image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
video_extensions = [".webm", ".mpg", ".mp4", ".avi", ".mkv"]
audio_extensions = [".m4a", ".mp3", ".wav"]
document_extensions = [".doc", ".pdf", ".xls", ".ppt", ".txt"]

# For cut/copy and paste functionality
clipboard_file = None
clipboard_action = None
auto_move_enabled = True

# Function to move file to a destination directory
def move_file(src_path, dest_dir):
    try:
        filename = os.path.basename(src_path)
        dest_path = join(dest_dir, filename)
        move(src_path, dest_path)
        log_action(f"Moved '{filename}' to '{dest_dir}'")
        refresh_file_list()  # Update the file list after moving
    except Exception as e:
        log_action(f"Error moving file: {e}")

# Function to copy file to a destination directory
def copy_file(src_path, dest_dir):
    try:
        filename = os.path.basename(src_path)
        dest_path = join(dest_dir, filename)
        copy2(src_path, dest_path)
        log_action(f"Copied '{filename}' to '{dest_dir}'")
    except Exception as e:
        log_action(f"Error copying file: {e}")

# Logger function to update the log area in the GUI
def log_action(action):
    log_text.insert(END, f"{action}\n")
    log_text.see(END)

# Refresh the listbox to display current files in the source directory
def refresh_file_list():
    file_list.delete(0, END)
    files = listdir(source_dir)
    for f in files:
        file_list.insert(END, f)
    log_action("File list refreshed.")

# Automatically move file to its correct destination folder based on extension
def auto_move_file(entry):
    global auto_move_enabled
    if not auto_move_enabled:
        return  # Skip auto-move if disabled

    filename = os.path.basename(entry)
    ext = splitext(filename)[1].lower()

    # Check if file is already in one of the destination directories
    if os.path.dirname(entry) in [dest_dir_image, dest_dir_video, dest_dir_music, dest_dir_documents]:
        log_action(f"Skipped auto-moving '{filename}', already in the destination folder.")
        return

    # Proceed with auto-moving only if the file is directly in the source_dir
    if os.path.dirname(entry) == source_dir:
        if ext in image_extensions:
            move_file(entry, dest_dir_image)
        elif ext in video_extensions:
            move_file(entry, dest_dir_video)
        elif ext in audio_extensions:
            move_file(entry, dest_dir_music)
        elif ext in document_extensions:
            move_file(entry, dest_dir_documents)
        else:
            log_action(f"File type not supported for auto move: {filename}")

# Watchdog handler for automatic file movements
class MoverHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return  # Ignore directory changes

        refresh_file_list()
        with os.scandir(source_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    auto_move_file(entry.path)

# Function to cut a selected file
def cut_selected_file():
    global clipboard_file, clipboard_action
    selected_file = file_list.get(file_list.curselection())
    clipboard_file = join(source_dir, selected_file)
    clipboard_action = "cut"
    log_action(f"Cut selected: {selected_file}")

# Function to copy a selected file
def copy_selected_file():
    global clipboard_file, clipboard_action
    selected_file = file_list.get(file_list.curselection())
    clipboard_file = join(source_dir, selected_file)
    clipboard_action = "copy"
    log_action(f"Copied selected: {selected_file}")

# Function to paste the file to the current folder (source_dir)
def paste_file():
    global clipboard_file, clipboard_action, auto_move_enabled
    if clipboard_file and clipboard_action:
        try:
            auto_move_enabled = False  # Disable auto-move during paste

            filename = os.path.basename(clipboard_file)
            dest_path = join(source_dir, filename)  # Paste in the current directory

            if exists(dest_path):
                log_action(f"File '{filename}' already exists in the current folder.")
                return

            if clipboard_action == "cut":
                move(clipboard_file, dest_path)  # Move file to current directory
                log_action(f"Moved '{filename}' to '{source_dir}'")
            elif clipboard_action == "copy":
                copy2(clipboard_file, dest_path)  # Copy file to current directory
                log_action(f"Copied '{filename}' to '{source_dir}'")

            # Clear clipboard after paste
            clipboard_file = None
            clipboard_action = None

            refresh_file_list()  # Update the file list after pasting
        except Exception as e:
            log_action(f"Error pasting file: {e}")
        finally:
            auto_move_enabled = True  # Re-enable auto-move after paste
    else:
        log_action("No file selected for paste.")

# Function to delete a selected file
def delete_selected_file():
    selected_file = file_list.get(file_list.curselection())
    file_path = join(source_dir, selected_file)
    try:
        remove(file_path)
        log_action(f"Deleted file: {selected_file}")
        refresh_file_list()
    except FileNotFoundError:
        log_action(f"File not found: {selected_file}")

# Function to open file or folder on double click
def open_item(event):
    global source_dir
    selected_file = file_list.get(file_list.curselection())
    file_path = join(source_dir, selected_file)
    
    if os.path.isdir(file_path):  # If it's a directory, navigate inside it
        source_dir = file_path
        refresh_file_list()
        log_action(f"Opened folder: {selected_file}")
    elif os.path.isfile(file_path):  # If it's a file, open it
        try:
            os.startfile(file_path)  # Open the file with its associated application
            log_action(f"Opened file: {selected_file}")
        except Exception as e:
            log_action(f"Error opening file: {e}")

# Function to go back to the parent directory
def go_back():
    global source_dir
    parent_dir = os.path.dirname(source_dir)
    if parent_dir and os.path.exists(parent_dir):
        source_dir = parent_dir
        refresh_file_list()
        log_action(f"Returned to folder: {parent_dir}")

# Function to add a new subfolder
def add_subfolder():
    new_folder_name = simpledialog.askstring("New Folder", "Enter the name of the new folder:")
    if new_folder_name:
        new_folder_path = join(source_dir, new_folder_name)
        if not exists(new_folder_path):
            makedirs(new_folder_path)
            log_action(f"Created new folder: {new_folder_name}")
            refresh_file_list()
        else:
            log_action(f"Folder '{new_folder_name}' already exists.")

# Start the file observer for automatic file management
def start_observer():
    event_handler = MoverHandler()
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=True)  # Recursive monitoring
    observer.start()

# GUI Initialization
root = Tk()
root.title("File Manager")
root.geometry("600x500")

# Define a font
default_font = tkfont.Font(family="Arial", size=12)

# Define colors
bg_color = "#e8e8e8"  # Neutral background color
button_color = "#d3d3d3"  # Light grey button color

root.configure(bg=bg_color)

# Top Frame for file list
top_frame = Frame(root, bg=bg_color)
top_frame.pack(fill="x", padx=10, pady=10)

# Labels
Label(top_frame, text="Files in Source Directory:", bg=bg_color, font=default_font).pack(side="left")

# Listbox to display files
file_list = Listbox(top_frame, height=15, width=50, font=default_font)
file_list.pack(side="left", fill="y")
file_list.bind("<Double-Button-1>", open_item)  # Bind double click to open file/folder

# Scrollbar for the file list
scrollbar = Scrollbar(top_frame)
scrollbar.pack(side="right", fill="y")
file_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=file_list.yview)

# Action Buttons Frame
action_frame = Frame(root, bg=bg_color)
action_frame.pack(pady=10)

# Define button icons (neutral design without green)
cut_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/cut.png")
copy_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/copy.png")
paste_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/paste.png")
delete_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/delete.png")
back_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/back.png")
new_folder_icon = PhotoImage(file="C:/Users/SUMEDH/Downloads/fileManager2/icon/new_folder.png")

# Buttons for actions
Button(action_frame, image=cut_icon, command=cut_selected_file, bg=button_color).grid(row=0, column=0, padx=5)
Button(action_frame, image=copy_icon, command=copy_selected_file, bg=button_color).grid(row=0, column=1, padx=5)
Button(action_frame, image=paste_icon, command=paste_file, bg=button_color).grid(row=0, column=2, padx=5)
Button(action_frame, image=delete_icon, command=delete_selected_file, bg=button_color).grid(row=0, column=3, padx=5)
Button(action_frame, image=back_icon, command=go_back, bg=button_color).grid(row=0, column=4, padx=5)
Button(action_frame, image=new_folder_icon, command=add_subfolder, bg=button_color).grid(row=0, column=5, padx=5)

# Text area for logs
log_text = Text(root, height=10, width=70, font=default_font, bg="#f0f0f0")
log_text.pack(padx=10, pady=10)

# Start the file observer
start_observer()

# Refresh the list when the app starts
refresh_file_list()

# Start the GUI event loop
root.mainloop()
