from dotenv import load_dotenv
import subprocess
import sys



load_dotenv(override=True)
command = ["flask","run"]

result = subprocess.run(command)

