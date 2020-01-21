# Fuse Validator System Watcher
The system watcher python script can be used by FUSE validators to autonomously keep an eye on there validating hardware. 
The script will notify you via email if any of the thresholds have been breached to ensure that network down time is kept to
a minimum and to relieve the validator from having to check on their hardware as often.

# Depenedices
```
• Python 3
• PyQt5 - for threading and event queues
• psutil and shutils - for checking system resoruce usage
• ezgmail
• web3
• Fuse-Explorer-API
```

# How to use
1. Create a new gmail account
2. Enable the GMail API for the new gmail account https://developers.google.com/gmail/api/quickstart/python
3. Set up the config.ini file as you wish
4. Run the script on an OS with a GUI and web browser to authenticate the gmail account
5. Run the script on your VM with nohup
6. Sit back and validate :)
```
sudo nohup python3 validator_checker.py &
```

# Features
Monitor types:
```
• Average CPU usage
• Avaliable RAM
• Avaliable HDD space
• Docker container checking  (currently only checks it's running)
• ETH balance
```

Responds to email request using the following subject lines, the authorisedReceiver setting in the config file stops the response
from email request other than the one specified in the config file.
```
• "STATUS" - returns the current value of the monitors
• "THRESHOLD_GET" - returns the current threshold values
• "THRESHOLD_SET" - message body = <monitorType>=<new_value> - sets the monitor value to the new value
• "KILL" - exits the script
```

