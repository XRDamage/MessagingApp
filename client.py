import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog
from tkinter.ttk import Combobox
import random

# Server details
HOST = '34.118.123.98'
PORT = 9999

class Client:
    nicknames = []

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        msg = tkinter.Tk()
        msg.withdraw()

        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname:", parent=msg)

        self.gui_done = False
        self.running = True
        self.individual_chat_active = False
        self.target_client = None

        gui_thread = threading.Thread(target=self.gui_start)
        receive_thread = threading.Thread(target=self.receive)

        gui_thread.start()
        receive_thread.start()

    def gui_start(self):
        self.win = tkinter.Tk()
        self.win.title("Chatterbox")
        self.win.configure(bg="#0B3861")

        self.chat_label = tkinter.Label(self.win, text="Chat:")
        self.chat_label.config(font=("Arial", 20))
        self.chat_label.pack(padx=20, pady=10)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=10)
        self.text_area.config(state='disabled')

        self.msg_label = tkinter.Label(self.win, text="Message:")
        self.msg_label.config(font=("Arial", 20))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_button = tkinter.Button(self.win, text="Send", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.pack(padx=25, pady=10)

        self.private_chat_button = tkinter.Button(self.win, text="Private Chat", command=self.start_private_chat)
        self.private_chat_button.config(font=("Arial", 12))
        self.private_chat_button.pack(padx=25, pady=10)

        self.individual_chat_win = None
        self.target_combobox = None

        self.gui_done = True

        self.win.protocol("WM_DELETE_WINDOW", self.stop)

        self.animate_button(self.send_button)
        self.animate_button(self.private_chat_button)

        self.win.mainloop()

    def animate_button(self, button):
        button.bind("<Enter>", self.on_enter)
        button.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        event.widget.config(bg="#87CEEB")
        event.widget.config(relief=tkinter.SUNKEN)
        event.widget.config(font=("Arial", 14, "bold"))

    def on_leave(self, event):
        event.widget.config(bg="SystemButtonFace")
        event.widget.config(relief=tkinter.RAISED)
        event.widget.config(font=("Arial", 12))

    def fetch_online_users(self):
        self.sock.send('/online'.encode('utf-8'))

    def start_private_chat(self):
        self.fetch_online_users()

        if self.individual_chat_win is not None:
            self.individual_chat_win.lift()
        else:
            self.individual_chat_win = tkinter.Toplevel(self.win)
            self.individual_chat_win.title("Private Chat")

            self.target_label = tkinter.Label(self.individual_chat_win, text="Select a client:")
            self.target_label.config(font=("Arial", 14))
            self.target_label.pack(padx=20, pady=5)

            self.target_combobox = Combobox(self.individual_chat_win)
            self.target_combobox.pack(padx=20, pady=5)

            self.start_chat_button = tkinter.Button(self.individual_chat_win, text="Start Chat", command=self.start_individual_chat)
            self.start_chat_button.config(font=("Arial", 12))
            self.start_chat_button.pack(padx=25, pady=10)

            self.update_target_combobox()

            self.individual_chat_win.protocol("WM_DELETE_WINDOW", self.close_individual_chat_window)

    def update_target_combobox(self):
        clients = [nickname for nickname in self.nicknames if nickname != self.nickname]
        self.target_combobox['values'] = clients

    def start_individual_chat(self):
        self.target_client = self.target_combobox.get()
        self.text_area.delete("1.0","end")

        # Check if the target client is selected
        if not self.target_client:
            return

        if self.individual_chat_win is not None:
            self.individual_chat_win.destroy()
            self.individual_chat_win = None

        
        self.text_area.config(state='normal')
        self.text_area.delete("1.0", "end")
        self.text_area.insert('end', f"\nStarted individual chat with {self.target_client}\n")
        self.text_area.config(state='disabled')

        # Send a message to the server to start an individual chat
        self.sock.send(f'@start_individual_chat:{self.target_client}'.encode('utf-8'))

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.sock.send(self.nickname.encode('utf-8'))
                elif message.startswith('NICKLIST'):
                    self.nicknames = message.split(':')[1].split(',')
                    if self.individual_chat_active and self.target_combobox is not None:
                        self.update_target_combobox()
                elif message.startswith('@individual_chat:'):
                    sender, message = message[18:].split(':', 1)
                    if sender == self.target_client or sender == self.nickname:
                        self.text_area.config(state='normal')
                        self.text_area.insert('end', f'{sender}: {message}\n')
                        self.text_area.yview('end')
                        self.text_area.config(state='disabled')
                else:
                    if self.gui_done:
                        self.text_area.config(state='normal')
                        self.text_area.insert('end', message)
                        self.text_area.yview('end')
                        self.text_area.config(state='disabled')
            except ConnectionAbortedError:
                break
            except:
                print("Error")
                self.sock.close()
                break

    def write(self):
        message = self.input_area.get('1.0', 'end').strip()
        self.input_area.delete('1.0', 'end')

        if message == '/online':
            self.text_area.config(state='normal')
            self.text_area.insert('end', "Requesting online users...\n")
            self.text_area.config(state='disabled')
            self.sock.send(message.encode('utf-8'))
        elif self.individual_chat_active:
            self.sock.send(f'@individual_chat:{self.target_client}:{message}\n'.encode('utf-8'))
        else:
            self.sock.send(f'{message}\n'.encode('utf-8'))

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

if __name__ == '__main__':
    client = Client(HOST, PORT)
