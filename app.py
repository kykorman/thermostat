from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import Adafruit_DHT as dht
import time
import gpiozero as gpio
import json
import eventlet

h=""
t=""

controlDict = {}

app = Flask(__name__)

@app.before_first_request
def create_application():
    global controlDict, h, t

    controlDict['heatPin']=gpio.LED(26)
    controlDict['coolPin']=gpio.LED(20)
    controlDict['fanPin']=gpio.LED(21)

    controlDict['heatPin'].off()
    controlDict['coolPin'].off()
    controlDict['fanPin'].off()
    controlDict['hvacState'] = False


    #TODO replace with reading/writing as JSON
    with open('/root/thermo/settings.txt') as f:
        controlDict['hvacFan'] = f.readline().rstrip()
        controlDict['hvacMode'] = f.readline().rstrip()
        controlDict['hvacHeat'] = float(f.readline())
        controlDict['hvacCool'] = float(f.readline())

    if controlDict['hvacFan'] == "on":
        controlDict['fanPin'].on()
       
    def runHvac():
        global  controlDict, h, t

        controlDict['heatPin'].off()
        controlDict['coolPin'].off()
        controlDict['hvacState'] = False
        
        while True:
            ## print("HvacMode: {} fanMode: {} hvacState: {} hvacCoolTemp: {} hvacHeatTemp: {}".format(controlDict['hvacMode'], controlDict['hvacFan'], controlDict['hvacState'], controlDict['hvacCool'], controlDict['hvacHeat']))
            if(controlDict['hvacMode']=="heat" and t < controlDict['hvacHeat'] -0.75):
                #check if temp is lower
                if(controlDict['hvacFan'] != "on"):
                    controlDict['fanPin'].on()
                controlDict['hvacState'] = True
                time.sleep(5)

                controlDict['heatPin'].on()
                
                while(t < controlDict['hvacHeat'] +0.75 and controlDict['hvacMode'] == "heat"):
                    time.sleep(10)

                controlDict['heatPin'].off()
                time.sleep(5)
                controlDict['hvacState'] = False
                if(controlDict['hvacFan'] != "on"):
                    controlDict['fanPin'].off()


            elif(controlDict['hvacMode']=="cool" and t > controlDict['hvacCool'] + 0.75):
                #check if temp is lower
                if(controlDict['hvacFan'] != "on"):
                    controlDict['fanPin'].on()
                controlDict['hvacState'] = True
                time.sleep(5)

                controlDict['coolPin'].on()
                
                while(t > controlDict['hvacCool'] -0.75 and controlDict['hvacMode'] == "cool"):
                    time.sleep(10)

                controlDict['coolPin'].off()
                time.sleep(5)
                controlDict['hvacState'] = False
                if(controlDict['hvacFan'] != "on"):
                     controlDict['fanPin'].off()
            
            time.sleep(10)


    def checkSensors():
        global controlDict, h, t
        dhtPin = 4
        while True:
            h,temp = dht.read_retry(dht.DHT22, dhtPin)
            
            #Ensure kind of reasonable temp sensor values; if it errored, it would probably say -127 or 127
            temp = temp * (9/5) + 32
            if(temp>=40 and temp<=100):
                t = temp
            
            ## Debug sensor
            print('Temp={0:0.1f}*F  Humidity={1:0.1f}%'.format(temp,h))
            time.sleep(10) # only check sensor every 10 seconds    
        
    
    hvacThread = threading.Thread(target=runHvac)
    sensThread = threading.Thread(target=checkSensors)


    sensThread.start()
    time.sleep(5)
    hvacThread.start()

def withinTempRange(temp):
    if(temp >= 55 and temp <= 85):
        return True
    return False

@app.route('/')
def home():
    return render_template('home.html')

# Go to /temp/heat or /temp/cool to set temp without changing operating mode. Could be useful for things like smart home integration.
@app.route('/temp/<hvacHC>')
def tempSet(hvacHC):
    global controlDict

    temp = request.args.get('temp', default = None, type = float)
    if(temp is not None and withinTempRange(temp)):
        if(hvacHC == "heat"):
            controlDict['hvacHeat']=temp
        elif(hvacHC == "cool"):
            controlDict['hvacCool']=temp

    with open('/root/thermo/settings.txt', 'w') as f:
        f.write(controlDict['hvacFan'] + "\n")
        f.write(controlDict['hvacMode'] + "\n")
        f.write("{:.2f}\n".format(controlDict['hvacHeat']))
        f.write("{:.2f}\n".format(controlDict['hvacCool']))

    return redirect(url_for('home'))

@app.route('/heat')
def heat():
    global controlDict
    controlDict['hvacMode']="heat"
    controlDict['coolPin'].off()

    temp = request.args.get('temp', default = None, type = float)
    if(temp is not None and withinTempRange(temp)):
        controlDict['hvacHeat'] = temp

    with open('/root/thermo/settings.txt', 'w') as f:
        f.write(controlDict['hvacFan'] + "\n")
        f.write(controlDict['hvacMode'] + "\n")
        f.write("{:.2f}\n".format(controlDict['hvacHeat']))
        f.write("{:.2f}\n".format(controlDict['hvacCool']))

    return redirect(url_for('home'))

@app.route('/cool')
def cool():
    global controlDict
    controlDict['hvacMode']="cool"
    controlDict['heatPin'].off()

    temp = request.args.get('temp', default = None, type = float)
    if(temp is not None and withinTempRange(temp)):
        controlDict['hvacCool'] = temp

    with open('/root/thermo/settings.txt','w') as f:
        f.write(controlDict['hvacFan'] + "\n")
        f.write(controlDict['hvacMode'] + "\n")
        f.write("{:.2f}\n".format(controlDict['hvacHeat']))
        f.write("{:.2f}\n".format(controlDict['hvacCool']))

    return redirect(url_for('home'))

@app.route('/fan')
def fan():
    global controlDict

    if(controlDict['hvacFan'] == "auto"):
        controlDict['hvacFan'] = "on"
        controlDict['fanPin'].on()
    else:
        controlDict['hvacFan'] = "auto"
        if(not controlDict['hvacState']): 
            controlDict['fanPin'].off()

    with open('/root/thermo/settings.txt','w') as f:
        f.write(controlDict['hvacFan'] + "\n")
        f.write(controlDict['hvacMode'] + "\n")
        f.write("{:.2f}\n".format(controlDict['hvacHeat']))
        f.write("{:.2f}\n".format(controlDict['hvacCool']))

    return redirect(url_for('home'))
