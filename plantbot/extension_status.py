from os.path     import dirname
from dataclasses import dataclass

@dataclass
class ExtensionStatus:
	"""Describes the status of an extension"""

	name:       str  # Human readable name
	loaded:     bool # True if the extension is currently loaded, false otherwise
	full_path:  str  # Full path used to address the extension
	identifier: str  # The identifier of the extension

	@property
	def is_debug(self) -> bool:
		"""Returns true if the extension is a debug extension"""
		
		return '.debug.' in self.identifier

	@property
	def is_core(self) -> bool:
		"""Returns true if the extension is a core extension"""
		
		return '.core.' in self.identifier

	def to_dict(self) -> dict:
		"""Converts the extension status to a dictionary"""
		
		return {
			'name'       : self.name,
			'loaded'     : self.loaded,
			'full_path'  : self.full_path,
			'identifier' : self.identifier
		}

	def __str__(self) -> str:
		return self.name