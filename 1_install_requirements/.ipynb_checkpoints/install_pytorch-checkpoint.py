import subprocess
import os

print(subprocess.run(["sh 1_install_requirements/install_pytorch.sh"], shell=True))