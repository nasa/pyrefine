# Required Python Packages
* dash (at least version 1.11.0)
* plotly
There packages can be installed using `pip install plotly dash`.

# Exporting html figures or data from the GUI

If you export data or html figures, those will be in the directory that the GUI was launched from.

# Port Forwarding for running the GUI to monitor an adaptation on a remote machine

The following instructions assume the remote machine is setup to allow port forwarding.

1. In the ~/.ssh/config on your local machine, find the remote machine that you want to connect to.
1. Pick a unique port number to avoid accidently connecting to someone else's application. Usually a number in the 8000s is a good choice.
1. Add a line like `LocalForward 8060 localhost:8060` which will forward port 8060 on the remote to port 8060 on your local machine (127.0.0.1:8060).
1. ssh into your remote machine. In your bashrc file, add `export PORT=8060`. Then `source ~/.bashrc`
1. On the remote machine, when you launch one of the dash GUIs you'll see "Dash is running on http://127.0.0.1:8060". In a web browser on your local machine type 127.0.0.1:8060 in your address bar, and it will load the GUI running on the remote.
