# Laya Server

The first start downloads the multilingual Laya checkpoint into the persistent
`/data/huggingface` directory. A CPU with several GB of free memory and disk
space is required. Wait until the log reports that Uvicorn is listening on
port 8000 before configuring Laya Assistant.

Set an API key if port 8000 is reachable by other devices. Enter the same key
in Laya Assistant's configuration form. Keep this HTTP port on a trusted LAN.

In Laya Assistant, enter `http://<your Home Assistant host>:8000` as the Laya
server URL. The URL must be reachable from the Home Assistant Core process.
