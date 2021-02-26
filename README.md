# thermostat
Development work on a smart thermostat pi project

Uses `firefox -kiosk http://localhost:8080` in an Ubuntu startup applications command (added in 20.04 I believe). Also uses `@reboot gunicorn --chdir /root/thermo/ -c /root/thermo/guni.py --worker-class eventlet app:app&` to run the app on boot. End result, the gunicorn server starts on boot, and Firefox is opened full-screen with the interface.
