import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv(override=True)

client = OpenAI()
MODEL = ""
REFLECTION_TURNS = 3
TEMPERATURE = 1