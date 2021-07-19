import os
from gpiozero.exc import BadPinFactory
import speech_recognition as sr
import playsound
import requests
import gpiozero
import pyjokes
import datetime
import pprint
from time import sleep
from gtts import gTTS
from envyaml import EnvYAML

def printWhite(text):
    print("\033[97m {}\033[00m".format(text))

def printRed(text):
    print("\033[91m {}\033[00m".format(text))

config = EnvYAML("config.yml")

raspberryPiEnabled = config["raspberryPi"]["enabled"]

# Do not use these objects, please use the functions found below
_errorLED = None
_recognizingLED = None
_voiceLED = None

def setupRaspberryPi():
    if raspberryPiEnabled == True:
        try:
            gpiozero.pi_info()
        except BadPinFactory:
            print('This appears to not be a Raspberry Pi!')
            return False
        errorLEDPin = config["raspberryPi"]["errorLEDPin"]
        recognizingLEDPin = config["raspberryPi"]["recognizingLEDPin"]
        voiceLEDPin = config["raspberryPi"]["voiceLEDPin"]
        if errorLEDPin == None:
            printRed("Error: Please set the \"errorLEDPin:\" in \"config.yml\"")
            return False
        if recognizingLEDPin == None:
            printRed("Error: Please set the \"recognizingLEDPin:\" in \"config.yml\"")
            return False
        if voiceLEDPin == None:
            printRed("Error: Please set the \"voiceLEDPin:\" in \"config.yml\"")
            return False
        _errorLED = gpiozero.LED(errorLEDPin)
        _recognizingLED = gpiozero.LED(recognizingLEDPin)
        _voiceLED = gpiozero.LED(voiceLEDPin)
        return True
    else:
        return False

raspberryPi = setupRaspberryPi()

def errorLED(value):
    if raspberryPi:
        if value:
            _errorLED.on()
        else:
            _errorLED.off()

def recognizingLED(value):
    if raspberryPi:
        if value:
            _recognizingLED.on()
        else:
            _recognizingLED.off()

def voiceLED(value):
    if raspberryPi:
        if value:
            _voiceLED.on()
        else:
            _voiceLED.off()

energyThreshold = config["energyThreshold"]
if energyThreshold == None:
    printRed("Error: Please set the \"energyThreshold:\" in \"config.yml\"")
    energyThreshold = 300

listener = sr.Recognizer()

temperatureUnit = config["temperatureUnit"]
if temperatureUnit == "fahrenheit":
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"
elif temperatureUnit == "celsius":
    temperatureUnit = "C"
    temperatureUnitText = "celsius"
else:
    printRed("Error: Please set the \"temperatureUnit:\" in \"config.yml\"")
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"

def tts(text):
    tts = gTTS(text=text, lang="en")
    ttsFile = "tts.mp3"
    tts.save(ttsFile)
    playsound.playsound(ttsFile)
    os.remove("tts.mp3")

def removeHtmlTags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

now = datetime.datetime.now()

def getTime():
    timeNow = now.strftime("%I:%M %p")
    return timeNow

def getDate():
    dateNow = now.strftime("%A, %B %d")
    return dateNow

def getWeather():
    weatherRequest = requests.get("http://wttr.in/?format=j1")
    weatherData = weatherRequest.json()

    return weatherData["current_condition"][0]

def getWikipedia(query):
    wikipediaRequest = requests.get("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=description|info&list=search&utf8=1&srsearch=" + query + "&srsort=relevance")
    wikipediaData = wikipediaRequest.json()

    return wikipediaData["query"]["search"]

def getVoiceInput():
    with sr.Microphone() as source:
        voiceLED(True)
        print("Listening...")
        listener.pause_threshould = 1
        listener.dynamic_energy_threshold = False
        listener.energy_threshold = energyThreshold
        voice = listener.listen(source)
        voiceLED(False)
    try:
        print("Recognizing...")
        recognizingLED(True)
        voiceInput = listener.recognize_google(voice, language ="en-us")
        recognizingLED(False)
        print("Raw Voice Input: " + voiceInput)
        voiceInput = voiceInput.lower()
        voiceInput = voiceInput.split(" ")
    except Exception as e:
        print(e)
        return "None"

    return voiceInput

def runAssist():
    voiceInput = getVoiceInput()
    if "assist" in voiceInput:
        playsound.playsound("Assets/recognition.wav")
        voiceInput = getVoiceInput()
        if "time" in voiceInput:
            timeNow = getTime()
            printWhite("Time: " + timeNow)
            tts("the current time is " + timeNow)
        elif "date" in voiceInput:
            dateNow = getDate()
            printWhite("Date: " + str(dateNow))
            tts("the current date is " + dateNow)
        elif "weather" in voiceInput:
            try:
                currentWeather = getWeather()
                temp = currentWeather["temp_" + temperatureUnit]
                feelsLike = currentWeather["FeelsLike" + temperatureUnit]
                humidity = currentWeather["humidity"]
                weatherDesc = currentWeather["weatherDesc"][0]["value"]
                printWhite("Weather Description: " + weatherDesc)
                printWhite("Temperature: " + temp + "°" + temperatureUnit)
                printWhite("Feels Like: " + feelsLike + "°" + temperatureUnit)
                printWhite("Humidity: " + humidity + "%")
                tts("It is " + weatherDesc + "at" + temp + "°" + temperatureUnitText + ",feels like " + feelsLike + ", with a humidity of " + humidity + "%")
            except Exception as e:
                errorLED(True)
                printRed("Error: " + e)
                tts("an issue occurred getting weather, please try again later")
                errorLED(False)
        elif "repeat" in voiceInput[0]:
            voiceInput.pop(0)
            voiceInput = " ".join(voiceInput)
            printWhite("User Said: " + voiceInput)
            tts(voiceInput)
        elif "wiki" in voiceInput[0] or "wikipedia" in voiceInput[0] or "search" in voiceInput[0] or "google" in voiceInput[0] or "search for" in voiceInput[0]:
            voiceInput.pop(0)
            voiceInput = " ".join(voiceInput)
            try: 
                wikipedia = getWikipedia(voiceInput)
                wikiPage = wikipedia[0]
                wikiSnippet = removeHtmlTags(wikiPage["snippet"])
                wikiTitle = wikiPage["title"]
                printWhite("Snippet for " + wikiTitle + ":" + "\n" + wikiSnippet)
                tts("according to wikipedia, " + wikiSnippet)
            except Exception as e:
                errorLED(True)
                printRed("Error: " + e)
                tts("an issue occurred getting wikipedia, please try again later")
                errorLED(False)
        elif "joke" in voiceInput:
            joke = pyjokes.get_joke()
            printWhite("Joke: " + joke)
            tts(joke)
        elif "exit" in voiceInput or "stop" in voiceInput:
            printWhite("Exiting...")
            tts("exiting, goodbye")
            playsound.playsound("Assets/exit.wav")
            exit()
        else:
            errorLED(True)
            printRed("Error: Command not recognized")
            tts("i did not get that, can you please try again")
            errorLED(False)
        playsound.playsound("Assets/exit.wav")

while True:
    runAssist()
