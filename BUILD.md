python3.10 -m venv venv
venv/bin/python3.10 -m pip install -r requirements.txt
venv/bin/python3.10 -m uvicorn api:app --host 0.0.0.0 --port 8000

sudo apt install texlive-latex-base
sudo apt install texlive-latex-extra

sudo mkdir /opt/openmagnetics
sudo chmod -R 777 /opt/openmagnetics