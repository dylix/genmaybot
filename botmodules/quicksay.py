def __init__(self):
	return

# --- Commands in this module

def nick(self, event):
	event.output += "Did you know you can change your name using \"/nick new_name\"?"
	return event
nick.command = "!nick"

def data(self, event):
	event.output += "Dont ask to ask, just ask."
	return event
data.command = "!data"

def bfy(self, event):
	event.output += "Because fuck you, thats why."
	return event
bfy.command = "!bfy"

# --- End commands
