# NLP

This service is the main form of communication between the user and the application. It listens for a trigger phrase
"Hey Chef" and then listen for an action to execute. This service also has an api to convert plain text into
words to send to the speaker to then be transmited to the user


Compilation on Windows (and probably iOS):
	pip install SpeechRecognition
	pip install pyttsx
	pip install requests
	pip install Flask
	
Compilation and Setup on RPi:
	pip install SpeechRecognition

	sudo apt-get install portaudio19-dev
	sudo apt-get install libasound-dev
	pip install pyaudio --user (needs to be 0.2.11)
	
	pip install pyttsx --user
	sudo apt-get install espeak
	sudo apt-get install flac
	
	pip install requests
	pip install Flask
	
	sudo apt-get install swig
	#sudo apt-get install libpulse-dev
	sudo apt-get install python-dev
	sudo pip install pocketsphinx
	
	sudo apt -y install python-pyaudio python3-pyaudio sox python3-pip python-pip libatlas-base-dev
	SNOWBOY: Download tar file from PyPi, extract, and in extracted folder run "sudo python setup.py install"
	
	FIX JACK ISSUE:
		sudo apt-get install multimedia-jack
		sudo dpkg-reconfigure -p high jackd2
		#If "broken or not fully installed": first do "sudo apt-get install jackd2"
		sudo adduser $(whoami) audio
		After reboot: pulseaudio --kill
		jack_control start
	
	Audio Setup:
		Go to: /usr/share/alsa/alsa.conf
		 - Change "0" to "1" in line: defaults.ctl.card 0
		 - Change "0" to "1" in line: defaults.pcm.card 0
		Set audio output to USB device (Andrea Communications...)
		
	
Running:
	Testing: python commands_test.py
	
Import class:
	import NLP