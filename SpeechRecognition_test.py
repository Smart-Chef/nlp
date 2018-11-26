
import os
import datetime
import speech_recognition as sr
import requests
import pyttsx
import json
from flask import Flask
import threading
from time import sleep
import signal
import math
#import RPi.GPIO as GPIO
import subprocess

END_VOCAB = ["EXIT", "END PROGRAM", "END", "STOP"]
COMMAND_VOCAB = ["SET", "TURN", "NEXT", "MOVE", "GO", "PREVIOUS", "LAST", "HELP", "START", "TAKE"]
TIME_VOCAB = ["TIME", "MINUTES", "HOW LONG", "SECONDS", "HOURS", "HOW MUCH LONGER", "ALARM", "WHEN"]
TEMP_VOCAB = ["HEAT", "TEMPERATURE", "HOT", "FAHRENHEIT", "DEGREE"]
WEIGHT_VOCAB = ["WEIGHT", "HEAVY"]
RECIPE_VOCAB = ["STEP", "DISH", "UTENSIL", "NEED"]

GLOBAL_IP = "10.230.77.127"

class Utensil:
    def __init__(self, _name, _id):
        self.name = _name
        self.id = _id
        self.inUse = False


class Quantity:
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit


class Ingredient:
    def __init__(self, _name, _quantity, _id):
        self.name = _name
        self.quantity = _quantity
        self.id = _id

    def parse_quantity(self, quantity):
        return Quantity(quantity, quantity)


class Step:
    def __init__(self):
        self.ingredients = []
        self.utensils = []
        self.text = []


class StoveDriver:
    def __init__(self):
        self.pin_assignments = {"keep_warm": None,
                                "medium": None,
                                "high": None,
                                "decrease": None,
                                "increase": None,
                                "start": None}
        self.GPIO_setup(self.pin_assignments.values())

    def GPIO_setup(self, pin_list):
        print "Set up GPIO"
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        #for pin in pin_list:
        #    GPIO.setup(pin, GPIO.OUT)
        #    GPIO.output(pin, GPIO.HIGH)  # Close relay

    def set_temp(self, temp):
        print "Setting temp to " + str(temp) + " degrees"

    def press_button(self, button):
        try:
            self.blink_pin(self.pin_assignments[button])
        except KeyError:
            print "ERROR!: " + button + " is an invalid button"

    def blink_pin(self, pin):
        self.GPIO_setup(self.pin_assignments.values())
        print "Blink pin " + str(pin)
        #GPIO.output(pin, GPIO.LOW)
        #sleep(0.1)
        #GPIO.output(pin, GPIO.HIGH)
        #GPIO.cleanup()


class Value:
    def __init__(self, _quantity=0, _units=""):
        self.quantity = _quantity
        self.units = _units

    def __str__(self):
        return str(self.quantity) + " " + self.units


class Timer:
    def __init__(self, _hours=0, _minutes=0, _seconds=0):
        self.hours = _hours
        self.minutes = _minutes
        self.seconds = _seconds

    def __str__(self):
        text = []
        if self.hours:
            text.append(str(self.hours) + " hours")
        if self.minutes:
            text.append(str(self.minutes) + " minutes")
        if self.seconds:
            text.append(str(self.seconds) + " seconds")
        return ", ".join(text)

    def get_time(self):
        return [self.hours, self.minutes, self.seconds]

    def set_hours(self, _hours):
        self.hours = _hours

    def set_minutes(self, _minutes):
        self.minutes = _minutes

    def set_seconds(self, _seconds):
        self.seconds = _seconds

class Speaker:
    def __init__(self):
        self.engine = pyttsx.init()

    def run(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

class SmartChef:
    def __init__(self, _server_ip):
        self.currDish = ""
        self.server_ip = _server_ip
        print("Testing server connection...")
        if not True:  # self.ping_server():
            print "Server ping failed"
            #raise(RuntimeError("Cannot connect to server: " + self.server_ip))
        else:
            print("Success!")
        self.stove = StoveDriver()
        self.currStep = 0
        self.utensils = []
        self.ingredients = []
        self.steps = []
        self.temp = Value()
        self.weight = Value()
        self.timer = Timer()
        #self.set_timer([0, 0, 30])
        #z = self.increment_step(1)
        #x = self.new_recipe()
        #y = self.set_alarm(datetime.datetime.now()+datetime.timedelta(seconds=30))
        #print("empty line")

    # Test server connection
    def ping_server(self):
        url = "http://" + self.server_ip + ":8001/api/ping"
        try:
            response = requests.request("GET", url)
        except requests.ConnectionError:
            return False
        print(response.text)
        return True

    def get_recipe(self, _recipe_id):
        url = "http://" + self.server_ip + ":8001/api/recipes/" + str(_recipe_id)
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['data']

    def get_number_steps(self, _recipe_id):
        return len(self.get_recipe(2)['steps'])

    def get_curr_recipe_id(self):
        url = "http://" + self.server_ip + ":8001/api/currentStep"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['recipe_id']

    def get_recipe_name(self, _recipe_id):
        return self.get_recipe(_recipe_id)['title']

    def get_curr_step(self):
        url = "http://" + self.server_ip + ":8001/api/currentStep"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['current_step']

    def get_curr_recipe(self):
        url = "http://" + self.server_ip + ":8001/api/currentStep"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['recipe_id']

    def get_prev_step(self):
        url = "http://" + self.server_ip + ":8001/api/currentStep"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['prev_step']

    def get_next_step(self):
        url = "http://" + self.server_ip + ":8001/api/currentStep"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['next_step']

    def get_recipe_ingredients(self, _recipe_id):
        url = "http://" + self.server_ip + ":8001/api/recipes/" + str(_recipe_id) + "/ingredients"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return [ingr['name'] for ingr in response_json['ingredients']]

    def get_step_ingredients(self, _recipe_id, _step_id):
        url = "http://" + self.server_ip + ":8001/api/recipes/" + str(_recipe_id) + "/ingredients/step/" + str(_step_id)
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        ingredient_list = []
        for ingr in response_json['ingredients']:
            new_qty = Quantity(ingr['step_info']['quantity'], ingr['step_info']['unit'])
            ingredient_list.append(Ingredient(ingr['name'], new_qty, ingr['id']))
        return ingredient_list

    def get_recipe_utensils(self, _recipe_id):
        url = "http://" + self.server_ip + ":8001/api/recipes/" + str(_recipe_id) + "/utensils"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        utensil_list = []
        for utensil in response_json['utensils']:
            utensil_list.append(Utensil(utensil['name'], utensil['id']))
        return utensil_list

    def get_step_utensils(self, _recipe_id, _step_id):
        url = "http://" + self.server_ip + ":8001/api/recipes/" + str(_recipe_id) + "/utensils/step/" + str(_step_id)
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        utensil_list = []
        for utensil in response_json['utensils']:
            utensil_list.append(Utensil(utensil['name'], utensil['id']))
        return utensil_list

    def get_temp(self):
        url = "http://" + self.server_ip + ":8000/api/getTemp"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['data']

    def get_weight(self):
        url = "http://" + self.server_ip + ":8000/api/getWeight"
        response = requests.request("GET", url)
        response_json = json.loads(response.text)
        return response_json['data']

    def get_timer(self):
        # TODO: Get timer from trigger queue
        return self.timer

    def set_alarm(self, date):
        url = "http://" + self.server_ip + ":8000/api/add/nlp"
        date_string = str(date.date())
        split_time = str(date.time()).split(".")
        if len(split_time) > 1:
            time_string = split_time[0] + "+" + split_time[1][0:2] + ":" + split_time[1][2:4]
        else:
            time_string = split_time[0] + "+00:00"
        param = date_string + "T" + time_string
        payload = {
            "service": "nlp",
            "action_key": "mockAction",
            "action_params": {
                "timer_finished": "False"
            },
            "trigger_keys": [
                "timer"
            ],
            "trigger_params": [
                param  # "2018-11-15T22:18:41+00:00"
            ]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, data=payload, headers=headers)
        response_json = json.loads(response.text)
        return response_json['data']

    def set_timer(self, time_array):
        hours = time_array[0]
        minutes = time_array[1]
        seconds = time_array[2]
        print "Setting timer:"
        print "HOURS: " + str(hours)
        print "MINUTES: " + str(minutes)
        print "SECONDS: " + str(seconds)
        date_difference = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        date = datetime.datetime.now() + date_difference
        self.set_alarm(date)

    def set_temp(self, _temp):
        print "Setting temp:"
        self.stove.set_temp(_temp[0])
        print str(_temp[0]) + _temp[1]

    def set_weight(self, _weight):
        print "Setting weight:"
        self.weight = Value(_weight[0], _weight[1])
        print str(_weight[0]) + _weight[1]

    def new_recipe(self):
        url = "http://" + self.server_ip + ":8001/api/initialize"
        payload = "{\"id\":1}"
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, data=payload, headers=headers)
        response_json = json.loads(response.text)
        return response_json['status'] == "success"

    def increment_step(self, increment_by):
        url = "http://" + self.server_ip + ":8001/api/increment-step"
        payload = "{\"increment_steps\": " + str(increment_by) + "}"
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, data=payload, headers=headers)
        response_json = json.loads(response.text)
        if response_json['status'] == "INVALID":
            raise RuntimeError("No active recipe")
        elif response_json['status'] == "success":
            # Return text for next step
            return response_json['step_info']


# Class containing all NLP operations and command dispatching
class NLP:
    # Initialize
    def __init__(self):
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        self.chef = SmartChef(GLOBAL_IP)
        self.server = self.server_setup()
        self.pid = os.getpid()
        signal.signal(signal.SIGINT, self.server_message_handler)
        self.exit_process = False
        self.first_file = True
        self.recording1_new = False
        self.recording2_new = False
        self.autorecord_thread = None
        self.pause_autorecord_flag = False
        self.autorecord_paused = False
        self.server_thread = self.init_server_thread()
        self.translation = ""
        self.speaker = pyttsx.init()  # TODO: Obsolete
        self.message_queue = []
        self.message_queue_lock = False
        self.audio_file_1 = sr.AudioFile('recording1.wav')
        self.audio_file_2 = sr.AudioFile('recording2.wav')
        self.command_audio = sr.AudioFile('command.wav')
        #self.chef.increment_step(1)

    def write_message_queue(self, msg):
        self.message_queue_lock = True
        self.message_queue.append(msg)
        self.message_queue_lock = False

    def read_message_queue(self):
        while self.message_queue_lock:
            sleep(1)
        return self.message_queue

    def check_for_messages(self):
        for msg in self.read_message_queue():
            self.annunciate(msg)
        self.clear_message_queue()

    def clear_message_queue(self):
        while self.message_queue_lock:
            sleep(1)
        self.message_queue = []

    def server_setup(self):
        app = Flask(__name__)

        @app.route('/send_message/<msg>')
        def receive_message(msg):
            # self.annunciate(msg)
            self.write_message_queue(msg)
            return "Pong"
        return app

    def init_server_thread(self):
        thread = threading.Thread(target=self.run_server)
        thread.setDaemon(True)
        thread.start()
        return thread

    def run_server(self):
        self.server.run(host='0.0.0.0')

    # Run full NLP loop
    def run_nlp(self):
        while self.translation.upper() not in END_VOCAB:
            while "HEY CHEF" not in self.translation.upper():
                self.check_for_messages()
                self.translation = self.DEPR_speech_to_text(ignition_phrase=True)
                print "Translation: " + self.translation
            self.annunciate("What do you want?")
            self.translation = self.DEPR_speech_to_text()
            print "Translation: " + self.translation
            self.parse_command(self.translation)

    def run_NLP_multithread(self):
        self.exit_process = False
        print ("Initializing autorecord thread")
        self.autorecord_thread = threading.Thread(target=self.endless_record)
        self.autorecord_thread.start()
        self.endless_process()
        print "Waiting for autorecord thread"
        self.autorecord_thread.join()

    def endless_record(self):
        print ("Beginning endless record")
        while not self.exit_process:
            print "  <-- RECORDING -->  "
            self.record_audio()
            print "  <-- DONE -->  "
        print "End audio recording thread"

    def endless_process(self):
        print ("Beginning endless process")
        while not self.exit_process:
            print "  -- PROCESSING --  "
            audio = self.get_autorecord()
            text = self.speech_to_text(audio)
            if text != "":
                self.process_text(text)
        print "End speech_to_text thread"

    def record_audio(self):
        # Pause autorecord if processing needs mic resources
        if self.pause_autorecord_flag:
            print "Auto record pausing"
            self.autorecord_paused = True
            # Wait until processing unit is done
            while self.pause_autorecord_flag:
                if self.exit_process:
                    return
                sleep(0.1)
            print "Resuming autorecord"
            self.autorecord_paused = False
        if self.first_file:
            subprocess.call(['arecord','--format=S16_LE','--duration=4','--rate=16000','--file-type=wav','recording1.wav'])
            self.recording1_new = True
        else:
            subprocess.call(['arecord','--format=S16_LE','--duration=4','--rate=16000','--file-type=wav','recording2.wav'])
            self.recording2_new = True
        # Alternate audio files
        self.first_file = not self.first_file
        #subprocess.call(['aplay','--format=S16_LE','--rate=16000','out.wav'])

    def record_command(self):
        subprocess.call(['arecord','--format=S16_LE','--duration=5','--rate=16000','--file-type=wav','command.wav'])
        with sr.AudioFile('command.wav') as source:
                audio = self.r.listen(source)
        return self.speech_to_text(audio)

    def get_autorecord(self):
        while not (self.recording1_new or self.recording2_new):
            print "Waiting for new recording..."
            sleep(0.1)
        audio = None
        if self.recording1_new:
            print "Reading recording 1"
            with sr.AudioFile('recording1.wav') as source:
                audio = self.r.listen(source)
            self.recording1_new = False
        elif self.recording2_new:
            print "Reading recording 2"
            with sr.AudioFile('recording2.wav') as source:
                audio = self.r.listen(source)
            self.recording2_new = False
        return audio

    def speech_to_text(self, audio):
        print ("Translating...")
        try:
            text = self.r.recognize_google(audio)
            print "TEXT: " + text
        except sr.UnknownValueError:
            text = ""
            print "ERROR: Unknown value"
        return text

    def process_text(self, text):
        if "okay cook" in text:
            print "Text recognized!"  # TODO: Add a *ding*
            self.pause_autorecord_flag = True
            self.text_to_speech("What would you like to do?")
            print "Waiting to pause autorecord..."
            while not self.autorecord_paused:
                sleep(0.1)
            print "Autorecord paused"
            command = ""
            while command == "":
                command = self.record_command()
            if "exit program" in command:
                self.exit_process = True
                return
            else:
                self.text_to_speech("Could not recognize command")
            self.pause_autorecord_flag = False

    # Record audio and attempt to translate to text
    def DEPR_speech_to_text(self, ignition_phrase=False):
        try:
            with self.mic as source:
                # ---- Translate input ---- #
                print "\nAdjusting for ambient noise..."
                self.r.adjust_for_ambient_noise(source)
                print "Listening..."
                if ignition_phrase:
                    audio = self.r.listen(source)
                    #audio = self.r.listen(source, timeout=3.0, phrase_time_limit=3.0)
                    # audio = self.r.listen(source, snowboy_configuration=["C:\Python27\Lib\site-packages\snowboy-1.2.0b1-py2.7.egg\snowboy", ["C:/Users/shfat/Documents/2018_Fall/CSCE_483/NLPTest/VoiceRecognition/hotword_models/HEY CHEF.pmdl"]])  # timeout after 5 seconds
                else:
                    audio = self.r.listen(source, timeout=3.0, phrase_time_limit=3.0)
                print "Got it! Translating..."
                return self.r.recognize_google(audio)
                #file = open("desktop.txt", "a")
                #file.write(text+"\n")
        except sr.UnknownValueError:
            if not ignition_phrase:
                self.annunciate("I did not understand you")
            return ""
        except sr.RequestError:
            if not ignition_phrase:
                self.annunciate("Recognition request failed")
            return ""

    # Provide text and audio response to user
    def annunciate(self, response, time=""):
        if time != "":
            time_split = time.split(":")
            hours = str(int(time_split[0]) % 12)
            minutes = time_split[1]
            seconds = str(int(float(time_split[2])))
            response += hours + " " + minutes + " and " + seconds + " seconds"
        print response
        self.text_to_speech(response)
        print "Done with text_to_speech"

    def wait_error_handler(self, signum, frame):
        raise RuntimeError("Error: Waited too long...")

    def server_message_handler(self, signum, frame):
        self.check_for_messages()

    # Translate text to audio output
    def text_to_speech(self, text):
        speaker_obj = Speaker()
        #signal.signal(signal.SIGALRM, self.wait_error_handler)
        #try:
        #    signal.alarm(3)
        #    speaker_obj.run(text)
        #    signal.alarm(0)
        #except RuntimeError as e:
        #    print e
        speaker_obj.run(text)
        del(speaker_obj)

    # Test if string is fully numeric
    def is_numeric(self, my_string):
        try:
            float(my_string)
            return True
        except ValueError:
            return False

    # Convert time array to float
    def time_to_float(self, time):
        time_float = time[0] * 60.0
        time_float = (time_float + time[1]) * 60.0
        time_float += time[2]
        return time_float

    # Parse input command and convert time value to time array
    def get_time_value(self, command_split):
        hours = 0
        minutes = 0
        seconds = 0
        units_array = ["hours", "minutes", "seconds"]
        for word_index, word in enumerate(command_split):
            if word == "O'CLOCK":
                command_split[word_index-1] = command_split[word_index-1] + ":00"
                command_split.pop(word_index)
        for word in command_split:
            if ":" in word:
                word_split = word.split(":")
                numeric = True
                for item in word_split:
                    if not item.isdigit():
                        numeric = False
                        break
                if numeric:
                    # Set all available values
                    for index in range(len(word_split)):
                        exec(units_array[index] + " = " + word_split[index])
                    break
        now = datetime.datetime.now()
        days = now.day
        # Adjust for AM/PM
        if now.hour > 12 and hours < 12:
            if (hours+12) > now.hour:
                hours = hours + 12
            else:
                days = now.day + 1
        return datetime.datetime(year=now.year, month=now.month, day=days, hour=hours, minute=minutes, second=seconds, microsecond=0)

    # Parse command for duration values to build time array
    def get_duration_value(self, command_split):
        hours = 0
        minutes = 0
        seconds = 0
        # Add up all time values
        for index, word in enumerate(command_split):
            hours_add = 0
            minutes_add = 0
            seconds_add = 0
            if "HOUR" in word:
                value_string = command_split[index - 1]
                if value_string.isdigit():
                    hours_add = int(value_string)
                elif self.is_numeric(value_string):
                    hours_add = int(float(value_string))
                    minutes_decimal = (float(value_string) - hours_add) * 60
                    minutes_add = int(minutes_decimal)
                    seconds_add = int((float(minutes_decimal) - minutes_add) * 60)
                else:
                    raise(RuntimeError("No valid hours value"))
            elif "MINUTE" in word:
                value_string = command_split[index - 1]
                if value_string.isdigit():
                    minutes_add = int(float(value_string))
                elif self.is_numeric(value_string):
                    minutes_add = int(float(minutes_add))
                    seconds_add = int((float(value_string) - minutes_add) * 60)
                else:
                    raise(RuntimeError("No valid minutes value"))
            elif "SECOND" in word:
                value_string = command_split[index - 1]
                if value_string.isdigit():
                    seconds_add = int(value_string)
                else:
                    raise(RuntimeError("No valid seconds value"))
            hours += hours_add
            minutes += minutes_add
            seconds += seconds_add
        # Final redistribution between units
        if hours or minutes or seconds:
            final_seconds = seconds % 60
            minutes += int(seconds / 60.0)
            final_minutes = minutes % 60
            final_hours = hours + int(minutes / 60.0)
        else:
            raise(RuntimeError("No time values"))
        return [final_hours, final_minutes, final_seconds]

    # Parse input command for temperature value
    def get_temp_value(self, command_split):
        for index, word in enumerate(command_split):
            if word == "DEGREES" or word == "FAHRENHEIT":
                return [int(command_split[index-1]), " " + word]

    # Parse input command for a given value type
    def get_value(self, command_split, setting):
        if setting == "duration":
            try:
                return self.get_duration_value(command_split)
            except RuntimeError as e:
                self.annunciate("Error: " + str(e))
                raise(RuntimeError("Error reading duration"))
        elif setting == "time":
            try:
                return self.get_time_value(command_split)
            except RuntimeError as e:
                self.annunciate("Error: " + str(e))
                raise(RuntimeError("Error reading time"))
        elif setting == "temp":
            return self.get_temp_value(command_split)
        else:
            raise(RuntimeError("Invalid setting"))

    # Clean all numeric words to digits
    def clean_numbers(self, command):
        word_numbers = {" ONE ": " 1 ",
                        " TWO ": " 2 ",
                        " THREE ": " 3 ",
                        " FOUR ": " 4 ",
                        " FIVE ": " 5 ",
                        " SIX ": " 6 ",
                        " SEVEN ": " 7 ",
                        " EIGHT ": " 8 ",
                        " NINE ": " 9 ",
                        " TEN ": " 10 ",
                        " ELEVEN ": " 11 ",
                        " TWELVE ": " 12 ",
                        " THIRTEEN ": " 13 ",
                        " FOURTEEN ": " 14 ",
                        " FIFTEEN ": " 15 ",
                        " SIXTEEN ": " 16 ",
                        " SEVENTEEN ": " 17 ",
                        " EIGHTEEN ": " 18 ",
                        " NINETEEN ": " 19 ",
                        " TWENTY ": " 20 ",
                        " THIRTY ": " 30 ",
                        " FORTY ": " 40 ",
                        " FIFTY ": " 50 ",
                        " SIXTY ": " 60 ",
                        " SEVENTY ": " 70 ",
                        " EIGHTY ": " 80 ",
                        " NINETY ": " 90 "}
        for item in word_numbers:
            command = command.replace(item, word_numbers[item])
        command_split = command.split()
        prev_numeric = False
        for index, word in enumerate(command_split):
            if word == "HUNDRED":
                prev_numeric = False
                command_split[index-1] = str(int(command_split[index-1]) * 100)
                command_split.pop(index)
                if (index + 2 < len(command_split)) and command_split[index+1] == "AND" and command_split[index+2].isdigit():
                    command_split[index-1] = str(int(command_split[index-1]) + int(command_split[index+2]))
                    command_split.pop(index+1)
                    command_split.pop(index+2)
            elif word.isdigit():
                if prev_numeric:
                    command_split[index - 1] = str(int(command_split[index - 1]) + int(word))
                    command_split.pop(index)
                    prev_numeric = False
                else:
                    prev_numeric = True
            else:
                prev_numeric = False
        command = " ".join(command_split)

        word_fractions = {"3 QUARTERS": ".75",
                          "HALF": ".5",
                          "QUARTER": ".25",
                          "THIRD": ".333333334"}
        for item in word_fractions:
            if item in command:
                command = command.replace(" AND A " + item, word_fractions[item])
                command = command.replace(" AND " + item, word_fractions[item])
                additional_phrases = ["ONE " + item, "A " + item + " OF AN", "A " + item, item + " OF AN", item + " AN", ]
                for phrase in additional_phrases:
                    if phrase in command:
                        command = command.replace(phrase, "0" + word_fractions[item])
        print "WITH CLEAN NUMBERS: " + command
        return command

    # Interpret command and dispatch appropriately
    def parse_command(self, text, test = False):
        # ---- Interpreter ---- #
        try:
            if text == "":
                return
            setting = "unknown"
            usage = "unknown"
            print text
            command = text.upper()
            command = self.clean_numbers(command)
            command_split = command.split()
            if "START RECIPE" in command or "NEW RECIPE" in command:
                self.annunciate("New recipe")
                if self.chef.new_recipe():
                    self.annunciate("What would you like to make?")
                # Initialize new recipe
                # Ask which recipe to make

            # REQUEST TYPE
            for word in COMMAND_VOCAB:
                if command_split[0] == word:
                    request_type = "command"
                    if word == "HELP":
                        setting = "search"
                    break
            else:
                request_type = "info"

            # SETTING
            # Time
            if setting == "unknown":
                for word in TIME_VOCAB:
                    if word in command:
                        setting = "time"
                        if "WHAT TIME" in command or "WHEN" in command or "ALARM" in command:
                            usage = "time"
                        else:
                            usage = "duration"
                        break
            if setting == "unknown":
                for word in TEMP_VOCAB:
                    if word in command:
                        setting = "temp"
                        break
            if setting == "unknown":
                for word in WEIGHT_VOCAB:
                    if word in command:
                        setting = "weight"
                        break
            if setting == "unknown":
                for word in RECIPE_VOCAB:
                    if word in command:
                        setting = "recipe"
                        if "STEP" in command:
                            usage = "step"
                        elif "NEED" in command:
                            usage = "supplies"
                        break
            if request_type == "command":
                if setting == "time":
                    if usage == "time":
                        self.annunciate("Set alarm")
                        value = self.get_value(command_split, "time")
                        self.chef.set_alarm(value)
                    elif usage == "duration":
                        value = self.get_value(command_split, "duration")
                        self.chef.set_timer(value)
                        text = "Set timer for "
                        units = [" HOURS ", " MINUTES ", " SECONDS "]
                        for index, timeval in enumerate(value):
                            if timeval > 0:
                                text += str(timeval) + units[index]
                        self.annunciate(text)
                elif setting == "temp":
                    #FIXME: set temp
                    value = self.get_value(command_split, "temp")
                    self.chef.set_temp(value)
                    self.annunciate("Set temp to " + str(value[0]) + value[1])
                elif setting == "recipe":
                    if "NEXT" in command:
                        self.annunciate(self.chef.increment_step(1))
                    elif "LAST" in command or "PREVIOUS" in command:
                        self.annunciate(self.chef.increment_step(-1))
                elif setting == "search":
                    #FIXME: Google search
                    self.annunciate("TODO: Add searching... ")
            elif request_type == "info":
                if setting == "time":
                    if usage == "time":
                        # get current time
                        timer = self.chef.get_timer().get_time()
                        _hours = timer[0]
                        _minutes = timer[1]
                        _seconds = timer[2]
                        date_finished = (datetime.datetime.now() +
                                         datetime.timedelta(hours=_hours, minutes=_minutes, seconds=_seconds))
                        time_finished = date_finished.time()
                        self.annunciate("Current time: ", str(datetime.datetime.now().time()))
                        self.annunciate("Timer done at : ", str(time_finished))
                    if usage == "duration":
                        self.annunciate("Time remaining: " + str(self.chef.get_timer()))
                elif setting == "temp":
                    self.annunciate("Current temp: " + self.chef.get_temp())
                elif setting == "weight":
                    self.annunciate(self.chef.get_weight())
                elif setting == "recipe":
                    if usage == "step":
                        if "NEXT" in command:
                            next_step = self.chef.get_next_step()
                            self.annunciate("Next step: " + next_step['data'])
                        elif "LAST" in command or "PREVIOUS" in command:
                            prev_step = self.chef.get_prev_step()
                            self.annunciate("Previous step: " + prev_step['data'])
                        elif "CURRENT" in command:
                            curr_step = self.chef.get_curr_step()
                            self.annunciate(curr_step['data'])
                    elif usage == "supplies":
                        if "INGREDIENTS" in command:
                            recipe_id = self.chef.get_curr_recipe()['id']
                            step_id = self.chef.get_curr_step()['id']
                            ingredients_list = self.chef.get_step_ingredients(recipe_id, step_id)
                            ingredients = [ingr.name for ingr in ingredients_list]
                            self.annunciate("Ingredients: " + ingredients.join(', '))
                            self.chef.get_step_ingredients()
                        elif "UTENSILS" in command or "TOOLS" in command:
                            self.annunciate("TODO: Give step utensils")
                        else:
                            self.annunciate("TODO: Give utensils and ingredients")
                else:
                    self.annunciate("Found no other options")
                    self.annunciate("TODO: Add searching...")
        except RuntimeError as e:
            self.annunciate("Error: " + str(e))
        except sr.RequestError:
            # API was unreachable or unresponsive
            self.annunciate("API unavailable")
        except sr.UnknownValueError:
            # speech was unintelligible
            self.annunciate("Unable to recognize speech")