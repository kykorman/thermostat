from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
from flask_socketio import SocketIO
import threading
import Adafruit_DHT as dht
import time
import gpiozero as gpio


h=""
t=""
hvacFan="auto"
hvacMode="cool"
hvacHeat=68.0
hvacCool=80.0

heatPin=""
coolPin=""
fanPin=""
dhtPin=4
hvacState = False
socketio=""

def create_application():
    global hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t
    global app
    global socketio
    heatPin=gpio.LED(26)
    coolPin=gpio.LED(20)
    fanPin=gpio.LED(21)
    dhtPin=4


    with open('/root/thermo/settings.txt') as f:
        hvacFan = f.readline()
        hvacMode = f.readline()
        hvacHeat = float(f.readline())
        hvacCool = float(f.readline())

       
    def runHvac():
        global  hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t

        heatPin.off()
        coolPin.off()
        time.sleep(20) # sleep for 10 seconds, check the sensor first
        while True:
            if(hvacMode=="heat" and t < hvacHeat -0.75):
                #check if temp is lower
                if(hvacFan != "on"):
                    fanPin.on()
                hvacState = True
                time.sleep(5)

                heatPin.on()
                
                while(t < hvacHeat +0.75):
                    time.sleep(10)

                heatPin.off()
                time.sleep(5)
                if(hvacFan != "on"):
                    fanPin.off()
                hvacState = False

            elif(hvacMode=="cool" and t > hvacCool + 0.75):
                #check if temp is lower
                if(hvacFan != "on"):
                    fanPin.on()
                hvacState = True
                time.sleep(5)

                coolPin.on()
                
                while(t > hvacCool -0.75):
                    time.sleep(10)

                coolPin.off()
                time.sleep(5)
                if(hvacFan != "on"):
                     fanPin.off()

                hvacState = False

    def checkSensors():
        global hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t
        while True:
            h,temp = dht.read_retry(dht.DHT22, dhtPin)
            #Print Temperature and Humidity on Shell window
            t = temp * (9/5) + 32
            print('Temp={0:0.1f}*F  Humidity={1:0.1f}%'.format(t,h))
            time.sleep(10) # only check sensor every 10 seconds
    hvacThread = threading.Thread(target=runHvac)
    sensThread = threading.Thread(target=checkSensors)


    sensThread.start()
    hvacThread.start()

def withinTempRange(temp):
    if(temp >= 55 and temp <= 85):
        return True
    return False

create_application()
app = Flask(__name__)

socketio = SocketIO(app)
print("Here")
socketio.run(app)

@app.route('/')
def home():

    return render_template('home.html')

@app.route('/heat')
def heat():
    global hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t
    hvacMode="heat"
    coolPin.off()

    temp = request.args.get('temp', default = None, type = float)
    if(temp is not None and withinTempRange(temp)):
        hvacHeat = temp

    with open('/root/thermo/settings.txt', 'w') as f:
        f.write(hvacFan + "\n")
        f.write(hvacMode + "\n")
        f.write("{:.2f}\n".format(hvacHeat))
        f.write("{:.2f}\n".format(hvacCool))
        
    return redirect(url_for('home'))

@app.route('/cool')
def cool():
    global hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t
    hvacMode="cool"
    heatPin.off()

    temp = request.args.get('temp', default = None, type = float)
    if(temp is not None and withinTempRange(temp)):
        hvacCool = temp

    with open('/root/thermo/settings.txt','w') as f:
        f.write(hvacFan + "\n")
        f.write(hvacMode + "\n")
        f.write("{:.2f}\n".format(hvacHeat))
        f.write("{:.2f}\n".format(hvacCool))
    return redirect(url_for('home'))

@app.route('/fan')
def fan():
    global hvacState, heatPin, coolPin, fanPin, dhtPin, hvacFan, hvacMode, hvacHeat, hvacCool, h, t

    if(hvacFan == "auto"):
        hvacFan = "on"
        fanPin.on()
    else:
        hvacFan = "auto"
        if(not hvacState): 
            fanPin.off()

    with open('/root/thermo/settings.txt','w') as f:
        f.write(hvacFan + "\n")
        f.write(hvacMode + "\n")
        f.write("{:.2f}\n".format(hvacHeat))
        f.write("{:.2f}\n".format(hvacCool))
    return redirect(url_for('home'))

