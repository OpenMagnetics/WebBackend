python3.10 -m venv venv
venv/bin/python3.10 -m pip install -r requirements.txt

sudo apt install texlive-latex-base
sudo apt install texlive-latex-extra
sudo apt install -y gnuplot

sudo apt-get install curl gnupg apt-transport-https -y

curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | sudo gpg --dearmor | sudo tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null
curl -1sLf https://github.com/rabbitmq/signing-keys/releases/download/3.0/cloudsmith.rabbitmq-erlang.E495BB49CC4BBE5B.key | sudo gpg --dearmor | sudo tee /usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg > /dev/null
curl -1sLf https://github.com/rabbitmq/signing-keys/releases/download/3.0/cloudsmith.rabbitmq-server.9F4587F226208342.key | sudo gpg --dearmor | sudo tee /usr/share/keyrings/rabbitmq.9F4587F226208342.gpg > /dev/null
sudo tee /etc/apt/sources.list.d/rabbitmq.list <<EOF
sudo apt-get update -y
sudo apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl
sudo apt-get install rabbitmq-server -y --fix-missing

sudo mkdir /opt/openmagnetics
sudo chmod -R 777 /opt/openmagnetics


    # Comment line 31 from /usr/share/freecad-daily/Mod/Draft/draftutils/params.py if it crashes at import
    # import Arch_rc


venv/bin/python3.10 -m uvicorn api:app --host 0.0.0.0 --port 8000
python3 -m celery -A plotter worker --loglevel=INFO