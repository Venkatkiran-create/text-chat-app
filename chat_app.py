import socket
import threading
import tkinter as tk
import sqlite3
from tkinter import messagebox, scrolledtext

# Set up the SQLite database
conn = sqlite3.connect("chat_app.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
conn.commit()

# Server Code
class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = []
        print("Server is running and waiting for connections...")

    def broadcast(self, message, client):
        for c in self.clients:
            if c != client:
                c.send(message)

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024)
                self.broadcast(message, client)
            except:
                self.clients.remove(client)
                client.close()
                break

    def receive_connections(self):
        while True:
            client, _ = self.server.accept()
            print("A client connected.")
            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client,)).start()

# Client Code with Tkinter GUI
class ChatClient:
    def __init__(self, master, username):
        self.master = master
        self.username = username
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(('127.0.0.1', 12345))

        # Setting up GUI
        master.title(f"Chat - {username}")
        master.geometry("400x500")
        
        self.chat_display = scrolledtext.ScrolledText(master, state='disabled', wrap='word')
        self.chat_display.pack(pady=10, padx=10)

        self.message_entry = tk.Entry(master, width=40)
        self.message_entry.pack(pady=5)

        send_button = tk.Button(master, text="Send", command=self.send_message)
        send_button.pack()

        # Start thread to receive messages
        threading.Thread(target=self.receive_messages).start()

    def send_message(self):
        message = f"{self.username}: {self.message_entry.get()}"
        self.message_entry.delete(0, tk.END)
        self.client.send(message.encode())
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{message}\n")
        self.chat_display.config(state='disabled')

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, f"{message}\n")
                self.chat_display.config(state='disabled')
            except:
                print("Disconnected from server.")
                break

# Authentication (Registration/Login)
def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return cursor.fetchone() is not None

# Tkinter Login Interface
def login_screen():
    def attempt_login():
        username = username_entry.get()
        password = password_entry.get()
        if login_user(username, password):
            login_window.destroy()
            start_client(username)
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")

    def attempt_register():
        username = username_entry.get()
        password = password_entry.get()
        if register_user(username, password):
            messagebox.showinfo("Registration Successful", "You can now log in.")
        else:
            messagebox.showerror("Registration Failed", "Username already exists.")

    login_window = tk.Tk()
    login_window.title("Chat Login")
    login_window.geometry("300x200")

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    login_button = tk.Button(login_window, text="Login", command=attempt_login)
    login_button.pack(pady=5)

    register_button = tk.Button(login_window, text="Register", command=attempt_register)
    register_button.pack(pady=5)

    login_window.mainloop()

# Starting the Client GUI
def start_client(username):
    root = tk.Tk()
    client_app = ChatClient(root, username)
    root.mainloop()

# To start the server or client
if __name__ == "__main__":
    choice = input("Enter 'server' to start as server or 'client' to start as client: ").strip().lower()
    if choice == 'server':
        server_app = ChatServer()
        server_app.receive_connections()
    elif choice == 'client':
        login_screen()
    else:
        print("Invalid choice. Please enter 'server' or 'client'.")
