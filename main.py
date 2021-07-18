import os
from gpiozero.exc import BadPinFactory
import speech_recognition as sr
import playsound
import requests
import gpiozero
import wikipedia
import pyjokes
import datetime
from time import sleep
from gtts import gTTS
from envyaml import EnvYAML
from gnews import GNews
import pprint

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
            print("\033[91m {}\033[00m".format("Error: Please set the \"errorLEDPin:\" in \"config.yml\""))
            return False
        if recognizingLEDPin == None:
            print("\033[91m {}\033[00m".format("Error: Please set the \"recognizingLEDPin:\" in \"config.yml\""))
            return False
        if voiceLEDPin == None:
            print("\033[91m {}\033[00m".format("Error: Please set the \"voiceLEDPin:\" in \"config.yml\""))
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
    print("\033[91m {}\033[00m".format("Error: Please set the \"energyThreshold:\" in \"config.yml\""))
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
    print("\033[91m {}\033[00m".format("Error: Please set the \"temperatureUnit:\" in \"config.yml\""))
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"

def tts(text):
    tts = gTTS(text=text, lang="en")
    ttsFile = "tts.mp3"
    tts.save(ttsFile)
    playsound.playsound(ttsFile)
    os.remove("tts.mp3")

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

def getVoiceInput():
    with sr.Microphone() as source:
        voiceLED(True)
        print("\033[97m {}\033[00m".format("Listening..."))
        listener.pause_threshould = 1
        listener.dynamic_energy_threshold = False
        listener.energy_threshold = energyThreshold
        voice = listener.listen(source)
        voiceLED(False)
    try:
        print("\033[97m {}\033[00m".format("Recognizing..."))
        recognizingLED(True)
        voiceInput = listener.recognize_google(voice, language ="en-us")
        recognizingLED(False)
        print("Raw Voice Input: " + voiceInput)
        voiceInput = voiceInput.lower()
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
            print("Time: " + timeNow)
            tts("the current time is " + timeNow)
        elif "date" in voiceInput:
            dateNow = getDate()
            print("Date: " + str(dateNow))
            tts("the current date is " + dateNow)
        elif "weather" in voiceInput:
            try:
                currentWeather = getWeather()
                temp = currentWeather["temp_" + temperatureUnit]
                feelsLike = currentWeather["FeelsLike" + temperatureUnit]
                humidity = currentWeather["humidity"]
                weatherDesc = currentWeather["weatherDesc"][0]["value"]
                print("Weather Description: " + weatherDesc)
                print("Temperature: " + temp + "°" + temperatureUnit)
                print("Feels Like: " + feelsLike + "°" + temperatureUnit)
                print("Humidity: " + humidity + "%")
                tts("It is " + weatherDesc + "at" + temp + "°" + temperatureUnitText + ",feels like " + feelsLike + ", with a humidity of " + humidity + "%")
            except Exception as e:
                errorLED(True)
                print("\033[91m {}\033[00m".format("Error: " + e))
                tts("an issue occurred getting weather, please try again later")
                errorLED(False)
        elif "repeat" in voiceInput:
            voiceInput = voiceInput.replace("repeat", "")
            print("User Said:" + voiceInput)
            tts(voiceInput)
        elif "wiki" in voiceInput or "wikipedia" in voiceInput or "search" in voiceInput or "google" in voiceInput or "search for" in voiceInput:
            voiceInput = voiceInput.replace("wikipedia", "").replace("wiki", "").replace("search", "").replace("google", "").replace("search for", "")
            try:
                wikiResults = wikipedia.summary(voiceInput, sentences=1, auto_suggest=False)
                print("Summary for:" + voiceInput + "\n" + wikiResults)
                tts("according to wikipedia, " + wikiResults)
                playsound.playsound("Assets/exit.wav")
            except Exception as e:
                errorLED(True)
                print("\033[91m {}\033[00m".format("Error: " + str(e)))
                tts("an issue occurred getting the wikipedia page, please try again later")
                errorLED(False)        
        elif "joke" in voiceInput:
            joke = pyjokes.get_joke()
            print("Joke: " + joke)
            tts(joke)
        elif "news" in voiceInput:
            google_news = GNews(max_results=5, period='1d')
            news = google_news.get_news('Linux')
            text = "In the news today, "
            for article in news:
                text = text + article["title"] + ", "
            print(text)
            tts(text)
        elif "exit" in voiceInput:
            print("Exiting...")
            tts("exiting, goodbye")
            playsound.playsound("Assets/exit.wav")
            exit()
        else:
            errorLED(True)
            print("Command not recognized")
            tts("i did not get that, can you please try again")
            errorLED(False)
        playsound.playsound("Assets/exit.wav")

while True:
    runAssist()
