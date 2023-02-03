import ctypes
import json
import os
import re
import smtplib
import subprocess
import tempfile
import webbrowser
from email.message import EmailMessage

import psutil
import pyperclip
import requests
import speech_recognition as sr
from mss import mss
from pydub import AudioSegment
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import *

from password import emailName, emailPassword

prev_msg = ''
email_reciver = ''
email_subject = ''
email_message = ''
class TelegramBot:
    def __init__(self):
        f = open('auth.json')
        auth = json.load(f)
        self.TOKEN = auth["TOKEN"]
        self.CHAT_ID = auth["CHAT_ID"]

    def start_command(self, update, context):
        buttons = [[KeyboardButton("⚠ Status ekranu")], [KeyboardButton("🔒 Zablokuj komputer")], [KeyboardButton("📸 Wykonaj Zrzut Ekranu")],
                   [KeyboardButton("✂ Wklej ze schowka")], [KeyboardButton(
                       "📄 Wypisz procesy")], [KeyboardButton("💤 Uśpij")],
                   [KeyboardButton("💡 Więcej komend")]]
        context.bot.send_message(
            chat_id=self.CHAT_ID, text="Zrobię to o co poprosisz.", reply_markup=ReplyKeyboardMarkup(buttons))

    def error(self, update, context):
        #wysłanie do konsoli dewelopera informacji o błędzie
        print(f"Update {update} caused error {context.error}")

    def send_email(self, reciver, subject, message):
        #konfiguracja SMTP GMail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        #połączenie
        server.starttls()
        #logowanie do GMail
        server.login(emailName, emailPassword)
        #formowanie wiadomości
        email = EmailMessage()
        email['From'] = 'Sender_Email'
        email['To'] = reciver
        email['Subject'] = subject
        email.set_content(message)
        #wysłanie wiadomości
        server.send_message(email)

    def take_screenshot(self):
        #pobranie tymczasowej ścieżki
        TEMPDIR = tempfile.gettempdir()
        #przemieszczenie się do ścieżki
        os.chdir(TEMPDIR)
        with mss() as sct:
            #wykonanie zrzutu ekranu
            sct.shot(mon=-1)
        #połączenie ścieżki wraz z nazwą zdjęcia i zwrócenie do wywołującej funkcji
        return os.path.join(TEMPDIR, 'monitor-0.png')
        

    def handle_message(self, update, input_text):
        global prev_msg
        global email_reciver
        global email_subject
        global email_message
        usr_msg = input_text.split()
        print('input_text', usr_msg)
        screenshotRegExp = "(?:^|\W)screenshot|rzut ekran|zrzut ekran|zrzut|rzut(?:$|\W)"
        lockRegExp = "(?:^|\W)zablokuj(?:$|\W)"
        browser = "(?:^|\W)otwórz|otwrz|open|stron(?:$|\W)"
        emailStartRegExp = "(?:^|\W)ema|email(?:$|\W)"
        if(prev_msg == 'email_start'):
            print('inside if')
            prev_msg = 'email_reciver'
            email_list = {
            'ja' : 'lizoo1999@gmail.com',
            'kolega': 'pawel.lizurej@yahoo.com',
            'pawe': 'pawel.lizurej@yahoo.com',
            }
            email_reciver=email_list[input_text]
            print(email_reciver)
            return 'Podaj temat emaila'
        if(prev_msg == 'email_reciver'):
            prev_msg = 'email_subject'
            email_subject = input_text
            print(email_subject)
            return 'Podaj treść emaila'
        if(prev_msg == 'email_subject'):
            prev_msg = ''
            email_message = input_text
            try:
                self.send_email(email_reciver, email_subject, email_message)
                return 'Email został wysłany. Sprawdź skrzynkę :)'
            except: 
                return 'Wystąpił błąd podczas wysyłania Email'
        if(re.search(emailStartRegExp, input_text)):
            prev_msg = 'email_start'
            return 'Podaj odbiorcę'
          
        if input_text == "wicej komend" or "wicej komend" in input_text:
            return """email <odbiorca temat wiadomość>\nurl <link>: otwórz link w przeglądarce\n"""

        if input_text == 'status ekranu' or "status ekranu" in input_text:
            for proc in psutil.process_iter():
                if (proc.name() == "LogonUI.exe"):
                    return 'Ekran jest zablokowany'
            return 'Ekran jest odblokowany'
       
        
        if re.search(lockRegExp,input_text):
            try:
                ctypes.windll.user32.LockWorkStation()
                return "Ekran zablokowany pomyślnie"
            except:
                return "Wystapił błąd podczas blokowania ekrnau"

        if re.search(screenshotRegExp, input_text):
            update.message.bot.send_photo(
                chat_id=self.CHAT_ID, photo=open(self.take_screenshot(), 'rb'))
            return None
        if re.search(browser, input_text):
            #regexp sprawdzający czy przetworzony głosowo tekst zawiera domenę strony 
            domainRegexp = "^([A-Za-z0-9]\.|[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]\.){1,3}[A-Za-z]{2,6}$"
            #odrzucenie pierwszej frazy, zawierającej słowo klcucz
            link_to_page = input_text.split(' ')[-1]
            #sprawdzanie czy adres jest pełny
            full_url = re.search(domainRegexp, link_to_page)
            if(full_url == None):
                #gdy adres nie jest pelny dodawana jest domena '.com'
                full_url = link_to_page + '.com'
            else:
                full_url = link_to_page
            try:
                #otwieranie strony internetowej z adresem url jako parametrem
                webbrowser.open(full_url)
                return 'Link otworzony pomyślnie'
            except:
                return 'Wystąpił błąd podczas otwierania linku'

        if input_text == "wklej ze schowka" or "wklej" in input_text:
            return pyperclip.paste()

        if input_text == "upij" or "uśpij" in input_text:
            try:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return "System został uśpiony"
            except:
                return "Nie można uśpić systemu sleep"

        if input_text == "wypisz procesy" or "procesy" in input_text:
            try:
                proc_list = []
                for proc in psutil.process_iter():
                    if proc.name() not in proc_list:
                        proc_list.append(proc.name())
                processes = "\n".join(proc_list)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            return processes

        if(usr_msg[0] == 'email'):
            self.send_email(usr_msg[1], usr_msg[2], usr_msg[3])

        if usr_msg[0] == 'url':
            try:
                webbrowser.open(usr_msg[1])
                return 'Link otworzony pomyślnie'
            except:
                return 'Wystąpił błąd podczas otwierania linku'

        

    def send_response(self, update, context, message = False):
        user_message = message or update.message.text
        #walidowanie czy użtkownik jest upoważniony do korzystania z bota
        if update.message.chat["username"] != "plizoo":
            print("[!] " + update.message.chat["username"] +
                  ' próbował użyć bota')
            context.bot.send_message(
                chat_id=self.CHAT_ID, text="Nic tu nie ma.")
        else:
            #przetwarzanie wiadomości użytkownika
            user_message = user_message.encode(
                'ascii', 'ignore').decode('ascii').strip(' ')
            user_message = user_message[0].lower() + user_message[1:]
            #wywołanie funkcji obsługiwania odpowiedzi
            response = self.handle_message(update, user_message)
            #wysyłanie odpowiedzi
            if response:
                if (len(response) > 4096):
                    for i in range(0, len(response), 4096):
                        context.bot.send_message(
                            chat_id=self.CHAT_ID, text=response[i:4096+i])
                else:
                    context.bot.send_message(
                        chat_id=self.CHAT_ID, text=response)
  
    def ogg2wav(self, ofn):
        wfn = ofn.replace('.ogg','.wav')
        x = AudioSegment.from_file(ofn)
        x.export(wfn, format='wav')    
    def get_voice(self, update, context: CallbackContext) -> None:
        new_file = context.bot.get_file(update.message.voice.file_id)
        # pobiera dźwięk jako plik
        new_file.download(f"voice_note.ogg")
        # odczytuje i przetwarza dźwięk
        self.ogg2wav(os.path.join(os.path.dirname(os.path.realpath(__file__)), "voice_note.ogg"))
        AUDIO_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "voice_note.wav")
        r = sr.Recognizer()
        # użycie pliku audio jako źródła
        with sr.AudioFile(AUDIO_FILE) as source:
            audio = r.record(source)  # odczytanie całego pliku audio
            try:
                #rozpoznanie dźwięku
                text = r.recognize_google(audio,language='pl-PL')
                print("Google Speech Recognition thinks you said " + text)
                #wysłanie odpowiedzi z powiedzianym tekstem do użytkownika
                update.message.reply_text('Powiedziałeś: ' + text)
                #uruchomienie docelowej funkcji
                self.send_response(update, context, text)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

    def start_bot(self):
        updater = Updater(self.TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(MessageHandler(Filters.voice, self.get_voice))
        dp.add_handler(MessageHandler(Filters.text, self.send_response))
        dp.add_error_handler(self.error)
        updater.start_polling()
        print("[+] BOT has started")
        updater.idle()


bot = TelegramBot()
bot.start_bot()