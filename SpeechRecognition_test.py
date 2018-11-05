

import datetime
import speech_recognition as sr

END_VOCAB = ["EXIT", "END PROGRAM", "END", "STOP"]
TIME_VOCAB = ["TIME", "MINUTES", "HOW LONG", "SECONDS", "HOURS", "HOW MUCH LONGER"]
OBJECT_VOCAB = ["DISH", "POT"]
COMMAND_VOCAB = ["SET", "TURN", "NEXT"]
INFO_VOCAB = ["HELP", "WHAT", "WHEN", "HOW MUCH"]


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

    def parseQuantity(self, quantity):
        return Quantity(quantity, quantity)


class Step:
    def __init__(self):
        self.ingredients = []
        self.utensils = []
        self.text = []


class SmartChef:
    def __init__(self):
        self.currDish = ""
        self.currStep = 0
        self.utensils = []
        self.ingredients = []
        self.steps = []
        self.temp = ""
        self.weight = ""
        self.timer = ""


class NLP:
    def __init__(self):
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        self.chef = SmartChef()
        self.translation = ''
        while self.translation.upper() not in END_VOCAB:
            self.speech_to_text()

    def speech_to_text(self):
        with self.mic as source:

            # ---- Translate input ---- #
            print "\nAdjusting for ambient noise..."
            self.r.adjust_for_ambient_noise(source)
            print "Listening..."
            audio = self.r.listen(source)
            print "Got it! Translating..."
            self.interpret_speech(audio)

    def getTimeValue(self, commandSplit):
        hours = 0
        minutes = 0
        seconds = 0
        for index, word in enumerate(commandSplit):
            if word == "hours":
                if commandSplit[index-1].isdigit():
                    hours = int(commandSplit[index-1])
                elif isNumeric(commandSplit[index-1]):
                    # TODO: translate float into respective time values
                    pass
                else:
                    pass
                    # TODO: set error flag
            elif word == "minutes":
                if commandSplit[index-1]:
                    minutes += int(commandSplit[index-1])
                else:
                    pass
                    # TODO: set error flag
            elif word == "seconds":
                if commandSplit[index-1]:
                    seconds +=  int(commandSplit[index-1])
                else:
                    pass
                    # TODO: set error flag
        else:
            pass
            # TODO: set error flag
        return [hours, minutes, seconds]

    def cleanNumbers(self, command):
        # TODO: translate all qualitative numerics to quantities
        return command

    def interpret_speech(self, audio):
        # ---- Interpreter ---- #
        try:
            requestType = "unknown"
            setting = "unknown"
            usage = "unknown"
            value = 0
            importantWords = []
            self.translation = self.r.recognize_sphinx(audio)
            print self.translation
            command = self.translation.upper()
            command = self.cleanNumbers(command)
            commandSplit = command.split()
            if "START RECIPE" in command or "NEW RECIPE" in command:
                print "New recipe"
                # Initialize new recipe
                # Ask which recipe to make

            # REQUEST TYPE
            for word in COMMAND_VOCAB:
                if word in command:
                    requestType = "command"
                    if word == "SET":
                        usage = "value"
                    elif word == "TURN":
                        usage = "binary"
                    elif word == "NEXT":
                        usage = "move"
                    break
            else:
                requestType = "info"

            # SETTING
            # Time
            for word in TIME_VOCAB:
                if word in command:
                    setting = "time"
                    if "WHAT TIME" in command or "WHEN" in command:
                        usage = "time"
                    else:
                        usage = "duration"
                    break
            # Object
            if setting == "unknown":
                for word in OBJECT_VOCAB:
                    if word in command:
                        setting = "object"
                        break
            if requestType == "command":
                if setting == "time":
                    if usage == "time":
                        print "Set time"
                    elif usage == "duration":
                        self.chef.timer = self.getTimeValue(commandSplit)
                    print "Set timer"
                elif setting == "temp":
                    #FIXME: set temp
                    self.chef.temp = value
                    print "Set temp"
                elif setting == "recipe":
                    #FIXME: move to next step
                    self.chef.currStep += 1
                    # update info to new step
                    print "Next step"
            elif requestType == "info":
                if setting == "time":
                    timeWords = [word for word in importantWords if word.setting == "time"][0]
                    if timeWords.usage == "time":
                        # get current time
                        print "Current time: " + str(datetime.datetime.now())
                    if timeWords.usage == "duration":
                        #FIXME: get timer
                        print "Time remaining: "
                elif setting == "temp":
                    #FIXME: get temp
                    print "Current temp: "
                elif setting == "recipe":
                    #FIXME: get next step
                    print "Next step: "
                elif setting == "search":
                    #FIXME: Google search
                    print "Searching for: "
        except sr.RequestError:
            # API was unreachable or unresponsive
            print "API unavailable"
        except sr.UnknownValueError:
            # speech was unintelligible
            print "Unable to recognize speech"
