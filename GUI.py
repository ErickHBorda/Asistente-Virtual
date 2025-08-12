import configparser
import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser
import scripts.addresses as addresses
from multiprocessing import Queue
from scripts.asistente_virtual import AssistantApp
import os
import signal

class AssistantGui:
    CONFIG_FILE = 'config.ini'
    CONFIG_SECTION = 'Assistant'

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.CONFIG_FILE)
        self.name = self.config.get(self.CONFIG_SECTION, 'name', fallback='ok')
        self.q = Queue()
        self.stop_event = None
        self.window_open = True
        self.api_key = self.config.get(self.CONFIG_SECTION, 'api_key')
        self.create_gui()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Asistente Virtual")
        self.root.geometry("500x450")
        self.root.configure(bg="#e9f5ff")
        self.root.resizable(False, False)
        self.root.iconbitmap('complementos/icon.ico')
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        font_title = ("Segoe UI", 11, "bold")
        font_normal = ("Segoe UI", 10)

        # Frame superior
        top_frame = tk.Frame(self.root, bg="#e9f5ff")
        top_frame.pack(pady=20)

        self.intro_label = tk.Label(
            top_frame,
            text=f'Tu asistente se llama "{self.name}". Pídele algo',
            font=font_title,
            bg="#e9f5ff"
        )
        self.intro_label.pack()

        # Botones iniciar/detener
        btn_frame = tk.Frame(self.root, bg="#e9f5ff")
        btn_frame.pack(pady=10)

        self.start_button = tk.Button(
            btn_frame, text="▶ Iniciar asistente", width=20,
            bg="#a8e6cf", fg="black", relief="flat", bd=0,
            font=font_normal, command=self.start
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(
            btn_frame, text="■ Detener asistente", width=20,
            bg="#f8d7da", fg="black", relief="flat", bd=0,
            font=font_normal, command=self.stop, state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=10)

        self.label_msg_temp = tk.Label(self.root, text='', bg="#e9f4ff", font=("Segoe UI", 9), fg="gray")
        self.label_msg_temp.pack()

        self.label_start = tk.Label(
            self.root, text='Presiona en "Iniciar asistente"',
            bg="#e9f5ff", font=font_normal
        )
        self.label_start.pack(pady=10)

        self.label_error = tk.Label(self.root, text='', foreground='red', bg="#e9f5ff")
        self.label_error.pack()

        hay_api = self.api_key != "0"

        self.lablel_api_key_state = tk.Label(
            self.root,
            text=f'API key {"guardada" if hay_api else "NO GUARDADA"}',
            foreground='green' if hay_api else 'red',
            font=font_title,
            bg="#e9f5ff"
        )
        self.lablel_api_key_state.pack(pady=(15, 0))

        api_frame = tk.Frame(self.root, bg="#e9f5ff")
        api_frame.pack(pady=10)

        self.label_api_key = tk.Label(
            api_frame, text=f'{"Cambiar" if hay_api else "Guardar"} API key:',
            bg="#e9f5ff", font=font_normal
        )
        self.label_api_key.grid(row=0, column=0, padx=(0, 5))

        self.api_key_entry = tk.Entry(api_frame, width=30, font=font_normal, bd=1, relief="solid")
        self.api_key_entry.grid(row=0, column=1, padx=(0, 5))

        self.save_api_key_button = tk.Button(
            api_frame, text='Cambiar' if hay_api else 'Guardar',
            command=self.save_api_key, bg="#d1ecf1", relief="flat", bd=0, font=font_normal
        )
        self.save_api_key_button.grid(row=0, column=2)

        # Botón para conseguir API key
        self.btn_conseguir_api_key = tk.Button(
            self.root, text="🌐 Conseguir API key",
            bg="#cce5ff", relief="flat", bd=0, font=font_normal,
            command=lambda: webbrowser.open("https://console.groq.com/keys ")
        )
        self.btn_conseguir_api_key.pack(pady=(10, 5))

        # Botón de ayuda
        self.help_button = tk.Button(
            self.root, text="❓ Ayuda", width=20,
            bg="#fff3cd", relief="flat", bd=0, font=font_normal,
            command=lambda: webbrowser.open(addresses.addresses["sourcecode"]["url"])
        )
        self.help_button.pack(pady=(5, 10))

        self.root.mainloop()

    def start(self):
        if self.api_key == "0":
            self.set_msg_temp('No se puede iniciar sin API key!')
            return

        self.label_start.config(text='Iniciando. Espere...')
        self.toggle_buttons('asistente_iniciado')

        self.stop_event = threading.Event()

        threading.Thread(target=AssistantApp, args=(self.q, self.stop_event, 0, self.api_key)).start()
        threading.Thread(target=self.read_output).start()

    def read_output(self):
        while True:
            msg = self.q.get().strip()
            if not self.window_open:
                break

            if "Detenido" in msg:
                self.toggle_buttons('asistente_detenido')
                self.label_start.config(text='Presiona en "Iniciar asistente"')
                self.label_msg_temp['text'] = ''
                break
            elif "Escuchando..." in msg:
                self.label_start.config(text='Escuchando...')
            elif 'Procesando...' in msg:
                self.label_start.config(text='Espere...')
            elif 'Internet no detectado. Reintentando...' in msg:
                self.label_start.config(text='Internet no detectado. Reintentando...')

    def stop(self):
        if self.stop_event is not None and not self.stop_event.is_set():
            self.stop_event.set()
            self.stop_button.config(state=tk.DISABLED)
            self.label_msg_temp['text'] = 'Escuchando por última vez y deteniendo...'

    def close_window(self):
        if messagebox.askokcancel("Cerrar", "¿Quieres cerrar el asistente?"):
            self.stop()
            self.window_open = False
            self.root.destroy()
            os.kill(os.getpid(), signal.SIGTERM)

    def change_value(self, clave: str, valor: str):
        self.config.set(self.CONFIG_SECTION, clave, valor)
        with open(self.CONFIG_FILE, 'w') as f:
            self.config.write(f)

    def set_msg_temp(self, msg: str):
        self.label_msg_temp['text'] = msg

        def reset_value():
            self.label_msg_temp['text'] = ''

        threading.Timer(5, reset_value).start()

    def toggle_buttons(self, estado: str):
        if estado == 'asistente_iniciado':
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.save_api_key_button.config(state=tk.DISABLED)
        elif estado == 'asistente_detenido':
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.save_api_key_button.config(state=tk.NORMAL)

    def save_api_key(self):
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            self.set_msg_temp('El campo de API Key no puede estar vacío')
            return

        # Guardar en config
        self.change_value('api_key', api_key)
        self.api_key = api_key
        self.api_key_entry.delete(0, tk.END)

        # Actualizar UI
        self.lablel_api_key_state['text'] = 'API key guardada'
        self.lablel_api_key_state['foreground'] = 'green'
        self.label_api_key['text'] = 'Cambiar API key:'
        self.save_api_key_button['text'] = 'Cambiar'

        self.set_msg_temp('API key guardada')


if __name__ == "__main__":
    app = AssistantGui()