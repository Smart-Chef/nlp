

import datetime
import speech_recognition as sr
import requests
import pyttsx

END_VOCAB = ["EXIT", "END PROGRAM", "END", "STOP"]
COMMAND_VOCAB = ["SET", "TURN", "NEXT", "MOVE", "GO", "PREVIOUS", "LAST", "HELP", "START"]
TIME_VOCAB = ["TIME", "MINUTES", "HOW LONG", "SECONDS", "HOURS", "HOW MUCH LONGER", "ALARM", "WHEN"]
TEMP_VOCAB = ["HEAT", "TEMPERATURE", "HOT", "FAHRENHEIT", "DEGREE"]
WEIGHT_VOCAB = ["WEIGHT", "HEAVY"]
RECIPE_VOCAB = ["STEP", "DISH", "UTENSIL", "NEED"]


class Utensil:
    def __init__(self, name):
        self.name = name
        self.inUse = False


class Quantity:
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit


class Ingredient:
    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

    def parse_quantity(self, quantity):
        return Quantity(quantity, quantity)


class Step:
    def __init__(self):
        self.ingredients = []
        self.utensils = []
        self.text = []

class Value:
    def __init__(self, _quantity = 0, _units = ""):
        self.quantity = _quantity
        self.units = _units

    def __str__(self):
        return str(self.quantity) + " " + self.units

class Timer:
    def __init__(self, _hours = 0, _minutes = 0, _seconds = 0):
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

class SmartChef:
    def __init__(self):
        self.currDish = ""
        self.currStep = 0
        self.utensils = []
        self.ingredients = []
        self.steps = []
        self.temp = Value()
        self.weight = Value()
        self.timer = Timer()

    def set_timer(self, time_array):
        hours = time_array[0]
        minutes = time_array[1]
        seconds = time_array[2]
        self.timer.set_hours(hours)
        self.timer.set_minutes(minutes)
        self.timer.set_seconds(seconds)
        print "Setting timer:"
        print "HOURS: " + str(hours)
        print "MINUTES: " + str(minutes)
        print "SECONDS: " + str(seconds)

    def get_temp(self):
        url = "http://10.231.75.28:8000/api/getTemp"
        response = "Test" #requests.request("GET", url)
        return response #.text

    def get_weight(self):
        url = "http://10.231.75.28:8000/api/getWeight"
        response = "Test" #requests.request("GET", url)
        return response #.text

    def get_timer(self):
        return self.timer

    def set_temp(self, _temp):
        print "Setting temp:"
        self.temp = Value(_temp[0], _temp[1])
        print str(_temp[0]) + _temp[1]

    def set_weight(self, _weight):
        print "Setting weight:"
        self.weight = Value(_weight[0], _weight[1])
        print str(_weight[0]) + _weight[1]

    def increment_step(self, increment_by):
        url = "http://10.231.75.28:8001/api/increment-step"
        payload = "{\"increment_steps\": " + str(increment_by) + "}"
        headers = {'Content-Type': 'application/json'}
        response = "Test" #requests.request("POST", url, data=payload, headers=headers)
        return response #.text


class ParsingError(RuntimeError):
    def __init__(self, _text):
        self.text = _text

    def __str__(self):
        return self.text


class NLP:
    def __init__(self):
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        self.chef = SmartChef()
        self.translation = ""
        self.speaker = pyttsx.init()

    def run_nlp(self):
        while self.translation.upper() not in END_VOCAB:
            while "HEY CHEF" not in self.translation.upper():
                self.translation = self.speech_to_text(ignition_phrase=True)
            self.annunciate("What do you want?")
            self.translation = self.speech_to_text()
            self.parse_command(self.translation)

    def speech_to_text(self, ignition_phrase = False):
        try:
            with self.mic as source:
                # ---- Translate input ---- #
                print "\nAdjusting for ambient noise..."
                self.r.adjust_for_ambient_noise(source)
                print "Listening..."
                #audio = self.r.listen(source, snowboy_configuration=["C:\Python27\Lib\site-packages\snowboy-1.2.0b1-py2.7.egg\snowboy", ["C:/Users/shfat/Documents/2018_Fall/CSCE_483/NLPTest/VoiceRecognition/hotword_models/HEY CHEF.pmdl"]])  # timeout after 5 seconds
                audio = self.r.listen(source, 5.0)
                print "Got it! Translating..."
                return self.r.recognize_google(audio)
                #file = open("desktop.txt", "a")
                #file.write(text+"\n")
        except sr.UnknownValueError:
            if not ignition_phrase:
                self.annunciate("I did not understand you")
            return ""

    def annunciate(self, response, time=""):
        if time != "":
            time_split = time.split(":")
            hours = str(int(time_split[0]) % 12)
            minutes = time_split[1]
            seconds = str(int(float(time_split[2])))
            response += hours + " " + minutes + " and " + seconds + " seconds"
        print response
        self.text_to_speech(response)

    def text_to_speech(self, text):
        self.speaker.say(text)
        self.speaker.runAndWait()

    def is_numeric(self, my_string):
        try:
            float(my_string)
            return True
        except ValueError:
            return False

    def time_to_float(self, time):
        time_float = time[0] * 60.0
        time_float = (time_float + time[1]) * 60.0
        time_float += time[2]
        return time_float

    def get_time_value(self, command_split):
        hours = 0
        minutes = 0
        seconds = 0
        units_array = ["hours", "minutes", "seconds"]
        for index, word in enumerate(command_split):
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
                        eval(units_array[index] + " = " + word_split[index])
                    break
        return [hours, minutes, seconds]

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
                    raise(ParsingError("No valid hours value"))
            elif "MINUTE" in word:
                value_string = command_split[index - 1]
                if value_string.isdigit():
                    minutes_add = int(float(value_string))
                elif self.is_numeric(value_string):
                    minutes_add = int(float(minutes_add))
                    seconds_add = int((float(value_string) - minutes_add) * 60)
                else:
                    raise(ParsingError("No valid minutes value"))
            elif "SECOND" in word:
                value_string = command_split[index - 1]
                if value_string.isdigit():
                    seconds_add = int(value_string)
                else:
                    raise(ParsingError("No valid seconds value"))
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
            raise(ParsingError("No time values"))
        return [final_hours, final_minutes, final_seconds]

    def get_temp_value(self, command_split):
        for index, word in enumerate(command_split):
            if word == "DEGREES" or word == "FAHRENHEIT":
                return [int(command_split[index-1]), " " + word]

    def get_value(self, command_split, setting):
        if setting == "duration":
            try:
                return self.get_duration_value(command_split)
            except ParsingError as e:
                self.annunciate("Error: " + str(e))
                raise(RuntimeError("Error reading duration"))
        elif setting == "time":
            try:
                return self.get_time_value(command_split)
            except ParsingError as e:
                self.annunciate("Error: " + str(e))
                raise(RuntimeError("Error reading time"))
        elif setting == "temp":
            return self.get_temp_value(command_split)
        else:
            raise(RuntimeError("Invalid setting"))


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

    def parse_command(self, text, test = False):
        # ---- Interpreter ---- #
        try:
            setting = "unknown"
            usage = "unknown"
            print text
            command = text.upper()
            command = self.clean_numbers(command)
            command_split = command.split()
            if "START RECIPE" in command or "NEW RECIPE" in command:
                self.annunciate("New recipe")
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
                        self.annunciate("TO DO: Set alarm")
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
                        self.annunciate("TODO: Move to next step")
                        self.chef.increment_step(1)
                    elif "LAST" in command or "PREVIOUS" in command:
                        self.annunciate("TODO: Move to previous step")
                        self.chef.increment_step(-1)
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
                            self.annunciate("TODO: Give next step: ")
                        elif "LAST" in command or "PREVIOUS" in command:
                            self.annunciate("TODO: Give previous step: ")
                    elif usage == "supplies":
                        if "INGREDIENTS" in command:
                            self.annunciate("TODO: Give step ingredients")
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