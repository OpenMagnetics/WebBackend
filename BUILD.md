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
## Provides modern Erlang/OTP releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu noble main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu noble main

# another mirror for redundancy
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu noble main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu noble main

## Provides RabbitMQ
##
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu noble main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu noble main

# another mirror for redundancy
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu noble main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu noble main
EOF
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
## Accounts feature (Phase 1, 2026-07)

Optional user accounts (cloud-saved designs, settings sync) live in
`app/backend/accounts/`. Requirements on top of the base install:

- Database schema is managed by Alembic: `alembic upgrade head`
  (connection from the same `OM_DB_*` environment variables).
- MAS validate-on-write needs the MAS and PEAS schema repos checked out
  (defaults: `../MAS/schemas` and `~/PSMA/PEAS/schemas`; override with
  `OM_MAS_SCHEMA_DIR` / `OM_PEAS_SCHEMA_DIR`).
- Transactional email (verification, password reset) is SMTP via Mailtrap:
  set `OM_SMTP_HOST`, `OM_SMTP_PORT`, `OM_SMTP_USER`, `OM_SMTP_PASSWORD`,
  `OM_SMTP_FROM` (and `OM_PUBLIC_URL` for the links). Without them the
  API runs fine but password reset returns 503.
- Session cookie is `__Host-`-prefixed + Secure when `OM_ENV=production`
  (requires HTTPS), plain `om_session` otherwise.

Tests: `pytest tests/test_accounts.py` (hits the real DB, self-cleaning).
