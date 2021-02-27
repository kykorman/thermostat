# thermostat
Development work on a smart thermostat Pi project

## How to run
Download the files to a directory, potentially using `git clone https://github.com/kykorman/thermostat.git`. I have placed the files at /root/thermo/ on my pi. The service file refers to this directory, change that file as needed.

Uses `firefox -kiosk http://localhost:8080` in an Ubuntu startup applications command (added in 20.04 I believe). This doesn't seem entirely consistent on reboots, sometimes doesn't open in full screen. Uses a systemd service script to run the gunicorn server at boot (have to enable with systemctl). End result, the gunicorn server starts on boot, and Firefox is opened full-screen with the interface.

## Materials
A Raspberry Pi (and storage)
A way to power the Pi (PoE or have it near an outlet)
A display (7 inch Pi display was used)
3 relays of sufficient spec for thermostat wiring
Wire that is sufficient for thermostat spec
DHT22 sensor for humidity/temp
