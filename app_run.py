from dotenv import load_dotenv
import subprocess
import sys

from event_hive_app.app import create_app

load_dotenv(override=True)
command = ["flask","run"]

result = subprocess.run(command)

