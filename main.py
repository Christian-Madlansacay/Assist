import os
from envyaml import EnvYAML
import speech_recognition as sr
from gtts import gTTS
import playsound
import datetime as date
from time import sleep
import requests
from gpiozero import LED

config = EnvYAML("config.yml")

raspberryPiEnabled = config["raspberryPi"]["enabled"]
if raspberryPiEnabled == True:
    errorLEDPin = config["raspberryPi"]["errorLEDPin"]
    recognizingLEDPin = config["raspberryPi"]["recognizingLEDPin"]
    voiceLEDPin = config["raspberryPi"]["voiceLEDPin"]
    if errorLEDPin == None:
        print("\033[91m {}\033[00m".format("Error: Please set the \"errorLEDPin:\" in \"config.yml\""))
    if recognizingLEDPin == None:
        print("\033[91m {}\033[00m".format("Error: Please set the \"recognizingLEDPin:\" in \"config.yml\""))
    if voiceLEDPin == None:
        print("\033[91m {}\033[00m".format("Error: Please set the \"voiceLEDPin:\" in \"config.yml\""))

state = config["state"]
if state == "":
    print("\033[91m {}\033[00m".format("Error: Please set the \"state:\" in \"config.yml\""))
    state = "newyork"

energyThreshold = config["energyThreshold"]
if energyThreshold == None:
    print("\033[91m {}\033[00m".format("Error: Please set the \"energyThreshold:\" in \"config.yml\""))
    energyThreshold = 300

listener = sr.Recognizer()

now = date.datetime.now()
dateNow = now.strftime("%A, %B %d")
timeNow = now.strftime("%I:%M %p")

temperatureUnit = config["temperatureUnit"]
if temperatureUnit == "fahrenheit":
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"
elif temperatureUnit == "celcius":
    temperatureUnit = "C"
    temperatureUnitText = "celcius"
else:
    print("\033[91m {}\033[00m".format("Error: Please set the \"temperatureUnit:\" in \"config.yml\""))
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"

weatherRequest = requests.get("http://wttr.in/" + state +"?format=j1") 
weatherData = weatherRequest.json()
temp = weatherData["weather"][0]["hourly"][0]["temp" + temperatureUnit]
feelsLike = weatherData["weather"][0]["hourly"][0]["FeelsLike" + temperatureUnit]
humidity = weatherData["weather"][0]["hourly"][0]["humidity"]
weatherDesc = weatherData["weather"][0]["hourly"][0]["weatherDesc"][0]["value"]

def tts(text):
    tts = gTTS(text=text, lang="en")
    ttsFile = "tts.mp3"
    tts.save(ttsFile)
    playsound.playsound(ttsFile)
    os.remove("tts.mp3")

def getVoiceInput():
    with sr.Microphone() as source:
        print("\033[97m {}\033[00m".format("Listening..."))
        listener.pause_threshould = 1
        listener.dynamic_energy_threshold = False
        listener.energy_threshold = energyThreshold
        voice = listener.listen(source)

    try:
        print("\033[97m {}\033[00m".format("Recognizing..."))
        voiceInput = listener.recognize_google(voice, language ="en-us")
        print("Raw Voice Input: " + voiceInput)
        voiceInput = voiceInput.lower()

    except Exception as e:
        print(e)
        return "None"

    return voiceInput

def runAssist():
    voiceInput = getVoiceInput()
    if "assist" in voiceInput:
        if raspberryPiEnabled == True:
            recognizingLEDPin.on()
            sleep(1)
            recognizingLEDPin.off()
            voiceLEDPin.on()
            tts("how can i help")
            sleep(1)
            voiceLEDPin.off()
        else:
            tts("how can i help")
        voiceInput = getVoiceInput()
        if "time" in voiceInput:
            if raspberryPiEnabled == True:
                recognizingLEDPin.on()
                sleep(1)
                recognizingLEDPin.off()
                voiceLEDPin.on()
                print("Time: " + timeNow)
                tts("the current time is " + timeNow)
                sleep(1)
                voiceLEDPin.off()
            else:
                print("Time: " + timeNow)
                tts("the current time is " + timeNow) 
        elif "date" in voiceInput:
            if raspberryPiEnabled == True:
                recognizingLEDPin.on()
                sleep(1)
                recognizingLEDPin.off()
                voiceLEDPin.on()
                print("Date: " + dateNow)
                tts("the current date is " + dateNow)
                sleep(1)
                voiceLEDPin.off()
            else:
                print("Date: " + dateNow)
                tts("the current date is " + dateNow)
        elif "weather" in voiceInput:
            if raspberryPiEnabled == True:
                recognizingLEDPin.on()
                sleep(1)
                recognizingLEDPin.off()
                voiceLEDPin.on()
                print("Weather Description: " + weatherDesc)
                print("Temperature: " + temp + "°" + temperatureUnit)
                print("Feels Like: " + feelsLike + "°" + temperatureUnit)
                print("Humidity: " + humidity + "%")
                tts(weatherDesc + "at" + temp + "°" + temperatureUnitText + "feels like " + feelsLike + " with a humidity of " + humidity + "%")
                sleep(1)
                voiceLEDPin.off()
            else:
                print("Weather Description: " + weatherDesc)
                print("Temperature: " + temp + "°" + temperatureUnit)
                print("Feels Like: " + feelsLike + "°" + temperatureUnit)
                print("Humidity: " + humidity + "%")
                tts(weatherDesc + "at" + temp + "°" + temperatureUnitText + "feels like " + feelsLike + " with a humidity of " + humidity + "%")
        elif "exit" in voiceInput:
            if raspberryPiEnabled == True:
                recognizingLEDPin.on()
                sleep(1)
                recognizingLEDPin.off()
                voiceLEDPin.on()
                print("Exiting...")
                tts("exiting, goodbye")
                sleep(1)
                voiceLEDPin.off()
                exit()
            else:
                print("Exiting...")
                tts("exiting, goodbye")
                exit()
        else:
            if raspberryPiEnabled == True:
                recognizingLEDPin.on()
                sleep(1)
                recognizingLEDPin.off()
                voiceLEDPin.on()
                print("Command not recognized")
                tts("i did not get that, can you please try again")
                sleep(1)
                voiceLEDPin.off()
                exit()
            else:
                print("Command not recognized")
                tts("i did not get that, can you please try again")

while True:
    runAssist()
