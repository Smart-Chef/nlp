# NLP

This service is the main form of communication between the user and the application. It listens for a trigger phrase
"Hey Chef" and then listen for an action to execute. This service also has an api to convert plain text into
words to send to the speaker to then be transmited to the user


Compilation on Windows (and probably iOS):
	pip install SpeechRecognition
	pip install pyttsx
	pip install requests
	
Compilation on RPi:
	pip install SpeechRecognition

	sudo apt-get install portaudio19-dev
	pip install pyaudio --user
	
	pip install pyttsx --user
	sudo apt-get install espeak
	sudo apt-get install flac
	
Running:
	Testing: python commands_test.py
	
Import class:
	import NLP