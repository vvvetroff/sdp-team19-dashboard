import inspect

def println(message: str) -> None:
	"""Prints a message with the current line number"""
	frame = inspect.currentframe().f_back
	line = frame.f_lineno if frame is not None else 0
	print(f"[{line}] {message}")
