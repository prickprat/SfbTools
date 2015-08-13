import sys
import logging
import argparse

argParser = argparse.ArgumentParser()
argParser.parse_args()

def printHelpText():
	helpText = """ Usage: 
	-h Prints the help text
	"""
	print(helpText)
