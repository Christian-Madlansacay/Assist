import os
import speech_recognition as sr
import playsound
import datetime as date
import requests
import gpiozero
from time import sleep
from gtts import gTTS
from envyaml import EnvYAML

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

def getWeather():
    weatherRequest = requests.get("http://wttr.in/?format=j1") 
    weatherData = weatherRequest.json()

    return weatherData["current_condition"][0]

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
            voiceLEDPin.on()
            tts("how can i help")
            sleep(1)
            voiceLEDPin.off()
            recognizingLEDPin.on()
        else:
            tts("how can i help")
        voiceInput = getVoiceInput()
        if "time" in voiceInput:
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                print("Time: " + timeNow)
                tts("the current time is " + timeNow)
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
            else:
                print("Time: " + timeNow)
                tts("the current time is " + timeNow) 
        elif "date" in voiceInput:
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                print("Date: " + dateNow)
                tts("the current date is " + dateNow)
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
            else:
                print("Date: " + dateNow)
                tts("the current date is " + dateNow)
        elif "weather" in voiceInput:
            currentWeather = getWeather()
            temp = currentWeather["temp_" + temperatureUnit]
            feelsLike = currentWeather["FeelsLike" + temperatureUnit]
            humidity = currentWeather["humidity"]
            weatherDesc = currentWeather["weatherDesc"][0]["value"]
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                print("Weather Description: " + weatherDesc)
                print("Temperature: " + temp + "°" + temperatureUnit)
                print("Feels Like: " + feelsLike + "°" + temperatureUnit)
                print("Humidity: " + humidity + "%")
                tts(weatherDesc + "at" + temp + "°" + temperatureUnitText + "feels like " + feelsLike + " with a humidity of " + humidity + "%")
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
            else:
                print("Weather Description: " + weatherDesc)
                print("Temperature: " + temp + "°" + temperatureUnit)
                print("Feels Like: " + feelsLike + "°" + temperatureUnit)
                print("Humidity: " + humidity + "%")
                tts(weatherDesc + "at" + temp + "°" + temperatureUnitText + "feels like " + feelsLike + " with a humidity of " + humidity + "%")
        elif "repeat" in voiceInput:
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                voiceInput = voiceInput.replace("repeat", "")
                print("User Said: " + voiceInput)
                tts(voiceInput)
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
            else:
                voiceInput = voiceInput.replace("repeat", "")
                print("User Said: " + voiceInput)
                tts(voiceInput)
        elif "exit" in voiceInput:
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                print("Exiting...")
                tts("exiting, goodbye")
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
                exit()
            else:
                print("Exiting...")
                tts("exiting, goodbye")
                exit()
        else:
            if raspberryPiEnabled == True:
                voiceLEDPin.on()
                print("Command not recognized")
                tts("i did not get that, can you please try again")
                sleep(1)
                voiceLEDPin.off()
                recognizingLEDPin.off()
            else:
                print("Command not recognized")
                tts("i did not get that, can you please try again")

while True:
    runAssist()
