from dotenv import load_dotenv
import subprocess

load_dotenv(override = True)

subprocess.run(["flask","run"])
