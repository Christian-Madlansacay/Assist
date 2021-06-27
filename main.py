from envyaml import EnvYAML
import speech_recognition as sr
import pyttsx3
import datetime as date
import requests

config = EnvYAML("config.yml")

errorCount = 0

voiceType = config["voiceType"]
if voiceType == "male":
    voiceType = 0
elif voiceType == "female":
    voiceType = 1
else:
    print("Error: Please set the \"voiceType:\" in \"config.yml\"")
    voiceType = 1
    errorCount = errorCount + 1

state = config["state"]
if state == "":
    print("Error: Please set the \"state:\" in \"config.yml\"")
    state = "newyork"
    errorCount = errorCount + 1

energyThreshold = config["energyThreshold"]
if energyThreshold == "":
    print("Error: Please set the \"energyThreshold:\" in \"config.yml\"")
    energyThreshold = 300
    errorCount = errorCount + 1

listener = sr.Recognizer()

ttsEngine = pyttsx3.init()
ttsVoices = ttsEngine.getProperty("voices")
ttsEngine.setProperty("voice", ttsVoices[voiceType].id)

now = date.datetime.now()
date = now.strftime("%A, %B %d")
time = now.strftime("%I:%M %p")

temperatureUnit = config["temperatureUnit"]
if temperatureUnit == "fahrenheit":
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"
elif temperatureUnit == "celcius":
    temperatureUnit = "C"
    temperatureUnitText = "celcius"
else:
    print("Error: Please set the \"temperatureUnit:\" in \"config.yml\"")
    temperatureUnit = "F"
    temperatureUnitText = "fahrenheit"
    errorCount = errorCount + 1

weatherRequest = requests.get("http://wttr.in/" + state +"?format=j1") 
weatherData = weatherRequest.json()
temp = weatherData["weather"][0]["hourly"][0]["temp" + temperatureUnit]
feelsLike = weatherData["weather"][0]["hourly"][0]["FeelsLike" + temperatureUnit]
humidity = weatherData["weather"][0]["hourly"][0]["humidity"]
weatherDesc = weatherData["weather"][0]["hourly"][0]["weatherDesc"][0]["value"]

def tts(text):
    ttsEngine.say(text)
    ttsEngine.runAndWait()

def getVoiceInput():
    with sr.Microphone() as source:
        print("Listening...")
        listener.pause_threshould = 1
        listener.dynamic_energy_threshold = False
        listener.energy_threshold = energyThreshold
        voice = listener.listen(source)

    try:
        print("Recognizing...")
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
        tts("how can i help")
        voiceInput = getVoiceInput()
        if "time" in voiceInput:
            print("Time: " + time)
            tts("the current time is " + time)
        elif "date" in voiceInput:
            print("Date: " + date)
            tts("the current date is " + date)
        elif "weather" in voiceInput:
            print("Weather Description: " + weatherDesc)
            print("Temperature: " + temp + "°" + temperatureUnit)
            print("Feels Like: " + feelsLike + "°" + temperatureUnit)
            print("Humidity: " + humidity + "%")
            tts(weatherDesc + "at" + temp + "°" + temperatureUnitText + "feels like " + feelsLike + " with a humidity of " + humidity + "%")
        elif "exit" in voiceInput:
            print("Exiting...")
            tts("exiting, goodbye")
            exit()
        else:
            print("Command not recognized")
            tts("i did not get that, can you please try again")

while True:
    runAssist()
