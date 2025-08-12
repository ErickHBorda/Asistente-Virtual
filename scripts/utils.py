import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import json
import time
import random
import numpy as np
from pygame import mixer
import pyautogui
##AGREGADO
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import webbrowser

from groq import Groq

from scripts.addresses import dir_mixer
from scripts.train_ai import train_ai

config = configparser.ConfigParser()
config.read('config.ini')

from groq import Groq

def key_press(rec: str, print_and_talk):
    rec_array = rec.split()
    index_tecla = rec_array.index('tecla')
    rec = rec_array[index_tecla+1] # Array rec a partir desde el momento que se dijo la palabra tecla

    teclas, contador = {'arriba' : "up", 'abajo' : "down", 'derecha' : 'right', 'izquierda' : 'left', 'espacio' : 'space', 'borrar' : 'backspace', 'enter' : 'enter', 'tab' : 'tab'}, 0
    for i in teclas:
        if rec == i:
            pyautogui.press(teclas[rec])
            print_and_talk('Hecho')
            break
        contador += 1
    if contador == len(teclas):
        pyautogui.press(rec)
        print_and_talk('Hecho')

def chronometer(state: str, chronometer: float | int, print_and_talk, humor: int | float, config):
    if state == "iniciar":
        print_and_talk('Iniciando cronómetro')
        chronometer = change_value(config, 'chronometer', time.time()) # Registra el tiempo actual
    else: # Cuando se detiene averigua cuánto tiempo pasó
        if chronometer == 0:
            print_and_talk('No puedes detener un cronómetro que no ha sido iniciado')
            if check_humor(humor): play_random_sound(['Ah_re_bolu', 'Estup', 'Imbec'], print_and_talk)
        else:
            tiempo_pasado = round(time.time() - chronometer) # Tiempo pasado en segundos

            dias_sr = tiempo_pasado/60/60/24 # el _sr significa que es el valor real
            dias = int(np.floor(dias_sr))

            horas_sr = (dias_sr - dias)*24
            horas = int(np.floor(horas_sr)) # Horas pasadas

            minutos_sr = (horas_sr - horas)*60
            minutos = int(np.floor(minutos_sr))

            segundos_sr = (minutos_sr - minutos)*60
            segundos = int(np.round(segundos_sr))

            string_res = 'Pasaron '
            if dias != 0:
                string_res += f'{dias} días '

            if horas != 0:
                string_res += f'{horas} horas '

            if minutos != 0:
                string_res += f'{minutos} minutos '

            if segundos != 0:
                if horas != 0 or minutos != 0 or dias != 0:
                    string_res += f'y {segundos} segundos'
                else:
                    string_res += f'{segundos} segundos'
            print_and_talk(string_res)
            chronometer = change_value(config, 'chronometer', 0)
    return chronometer

def play_sound(rec: str, print_and_talk, cantidad = 1): # Reproduce sonidos pedidos en formato mp3 que estén en "direccion_m"
    try:
        for i in dir_mixer:
            if i in rec:
                mixer.init()
                mixer.music.load(f"./complementos/audio/{dir_mixer[i]['nombre']}.mp3")
                mixer.music.set_volume(dir_mixer[i]['volumen'])
                mixer.music.play(cantidad) # mixer.music.play(n) suena n veces
                break
    except Exception:
        print_and_talk('Error, el archivo de sonido no está o no funciona')

def play_random_sound(opciones: list[str], print_and_talk):
    play_sound(random.choice(opciones), print_and_talk)

def check_humor(humor: int | float): # Agarra un número al azar y evalúa si se activa un comentario "gracioso" en algunos pedidos
    return 100 * random.random() < humor

def change_value(config, clave: str, valor: int | float): # Modifica el valor de un dato en config.ini
    config.set('Assistant', clave, str(valor))
    with open('config.ini', 'w') as f:
        config.write(f)
    return valor

def process_with_natural_language(rec: str, historial: list[dict[str, str]], api_key: str):
    client = Groq(
        api_key = api_key,
    )

    historial.append({"role": "user", "content": rec})

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages = historial,
        temperature=0,
        response_format={ "type": "json_object" }
    ).choices[0].message.content

    historial.append({
        "role": "assistant",
        "content": response
    })

    try: # En caso de que la respuesta no sea un json, tal como lo especifiqué
        return json.loads(response)
    except json.JSONDecodeError:
        return json.loads('{ "action": "none" }')

def process_with_natural_language_informal_talk(rec: str, historial: list[dict[str, str]], api_key: str):
    client = Groq(
        api_key = api_key,
    )

    historial.append({"role": "user", "content": rec})

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages = historial,
        temperature=0
    ).choices[0].message.content

    historial.append({
        "role": "assistant",
        "content": response
    })

    return response

def restart_ia(informal_chat: int, print_and_talk, api_key: str, stop): # Reinicia el historial de la IA y la vuelve a entrenar. Es más que nada para aquellos casos donde se detecta que ya no está respondiendo como debería
    print("----- IA reiniciada -----")
    return train_ai(informal_chat, print_and_talk, api_key, stop)




##########AGREGADO
def get_spotify_client():
    config = configparser.ConfigParser()
    config.read('config.ini')

    client_id = config.get('Spotify', 'client_id')
    client_secret = config.get('Spotify', 'client_secret')
    redirect_uri = config.get('Spotify', 'redirect_uri')

    print("📢 redirect_uri usado:", redirect_uri)  # ← Agrega esto para verificar

    scope = "user-read-playback-state user-modify-playback-state"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    ))
    return sp

CONTACTS_FILE = 'contactos.json'

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_contact(name, number):
    contacts = load_contacts()
    contacts[name.lower()] = number
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=4, ensure_ascii=False)

