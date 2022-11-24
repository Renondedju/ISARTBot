from dataclasses import dataclass

@dataclass
class DatabaseEventListener:
	""" A database event listener """

	instance: object   = None # The instance of the class that the listener is in
	name    : str      = None # The name of the event to listen for
	func    : callable = None # The function to call when the event is triggered