from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
import threading
import Adafruit_DHT as dht
import time
import gpiozero as gpio
import json



controlDict = {}
pinDict = {}
app = Flask(__name__)

@app.before_first_request
def create_application():
    global pinDict, controlDict

    pinDict['heatPin']=gpio.LED(26, active_high=False) #Set active_high to false so that the relays default to pins disconnect (instead of with no power, they short all circuits :/)
    pinDict['coolPin']=gpio.LED(20, active_high=False)
    pinDict['fanPin']=gpio.LED(21, active_high=False)

    pinDict['heatPin'].off()
    pinDict['coolPin'].off()
    pinDict['fanPin'].off()
    controlDict['hvacState'] = False


    #TODO replace with reading/writing as JSON
    with open('/root/thermo/settings.txt') as f:
        controlDict['hvacFan'] = f.readline().rstrip()
        controlDict['hvacMode'] = f.readline().rstrip()
        controlDict['hvacHeat'] = float(f.readline())
        controlDict['hvacCool'] = float(f.readline())

    if controlDict['hvacFan'] == "on":
        pinDict['fanPin'].on()
       
    def runHvac():
        global pinDict, controlDict

        pinDict['heatPin'].off()
        pinDict['coolPin'].off()
        controlDict['hvacState'] = False
        
        while True:
            ## print("HvacMode: {} fanMode: {} hvacState: {} hvacCoolTemp: {} hvacHeatTemp: {}".format(controlDict['hvacMode'], controlDict['hvacFan'], controlDict['hvacState'], controlDict['hvacCool'], controlDict['hvacHeat']))
            if(controlDict['hvacMode']=="heat" and controlDict['currTemp'] < controlDict['hvacHeat'] -0.5):
                #check if temp is lower
                if(controlDict['hvacFan'] != "on"):
                    pinDict['fanPin'].on()
                controlDict['hvacState'] = True
                time.sleep(5)

                pinDict['heatPin'].on()
                
                while(controlDict['currTemp'] < controlDict['hvacHeat'] +0.5 and controlDict['hvacMode'] == "heat"):
                    time.sleep(10)

                pinDict['heatPin'].off()
                time.sleep(5)
                controlDict['hvacState'] = False
                if(controlDict['hvacFan'] != "on"):
                    pinDict['fanPin'].off()


            elif(controlDict['hvacMode']=="cool" and controlDict['currTemp'] > controlDict['hvacCool'] + 0.5):
                #check if temp is lower
                if(controlDict['hvacFan'] != "on"):
                    pinDict['fanPin'].on()
                controlDict['hvacState'] = True
                time.sleep(5)

                pinDict['coolPin'].on()
                
                while(controlDict['currTemp'] > controlDict['hvacCool'] -0.5 and controlDict['hvacMode'] == "cool"):
                    time.sleep(10)

                pinDict['coolPin'].off()
                time.sleep(5)
                controlDict['hvacState'] = False
                if(controlDict['hvacFan'] != "on"):
                     pinDict['fanPin'].off()
    
            time.sleep(10)


    def checkSensors():
        global pinDict, controlDict
        
        dhtPin = 4
        while True:
            controlDict['currHumidity'], temp = dht.read_retry(dht.DHT22, dhtPin)
            
            #Ensure kind of reasonable temp sensor values; if it errored, it would probably say -127 or 127
            temp = temp * (9/5) + 32
            if(temp>=40 and temp<=100):
                controlDict['currTemp'] = temp
            
            ## Debug sensor
            # print('Temp={0:0.1f}*F  Humidity={1:0.1f}%'.format(temp,controlDict['currHumidity']))
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
    global pinDict, controlDict

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
    global pinDict, controlDict
    controlDict['hvacMode']="heat"
    pinDict['coolPin'].off()
    
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
    global pinDict, controlDict
    controlDict['hvacMode']="cool"
    pinDict['heatPin'].off()

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
    global pinDict, controlDict

    if(controlDict['hvacFan'] == "auto"):
        controlDict['hvacFan'] = "on"
        pinDict['fanPin'].on()
    else:
        controlDict['hvacFan'] = "auto"
        if(not controlDict['hvacState']): 
            pinDict['fanPin'].off()

    with open('/root/thermo/settings.txt','w') as f:
        f.write(controlDict['hvacFan'] + "\n")
        f.write(controlDict['hvacMode'] + "\n")
        f.write("{:.2f}\n".format(controlDict['hvacHeat']))
        f.write("{:.2f}\n".format(controlDict['hvacCool']))

    return redirect(url_for('home'))

@app.route('/data')
def retData():
    global pinDict, controlDict

    pinState = {}
    pinState['fanPin'] = pinDict['fanPin'].value
    pinState['heatPin'] = pinDict['heatPin'].value
    pinState['coolPin'] = pinDict['coolPin'].value

    return json.dumps({**controlDict, **pinState})
    #return render_template('data.html', currTemp="{:.1f}".format(controlDict['currTemp']))
@app.route('/off')
def turnOff():
    global controlDict, pinDict
    controlDict['hvacMode'] = "off" 

    return redirect(url_for('home'))


@app.route('/mode')
def toggleMode():
    global controlDict, pinDict

    if(controlDict['hvacMode']=="cool"):
        heat()
    elif(controlDict['hvacMode']=="heat"):
        turnOff()
    else:
        cool()
    
    return redirect(url_for('home'))

    

