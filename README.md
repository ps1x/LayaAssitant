# Laya Assistant

Laya Assistant is a local [Home Assistant](https://www.home-assistant.io/)
conversation agent. It asks a [Laya](https://pypi.org/project/laya/) server
three small questions in sequence: **capability → approved target → action**.
Only entities selected in the integration's configuration are available to the
assistant. Laya cannot submit an arbitrary Home Assistant entity ID or service.

The integration can turn selected lights, switches, fans, and climate devices
on or off; read selected temperature
sensors; and asking the current time. Lighting switches belong in the **Lights**
selector. Switches used for other purposes belong in **Other switches**. A
generic room-light request addresses the selected lights in that HA area;
fixture names address individual entities. Climate setpoints and unrelated HA
services are not supported in this first release.

The assistant automatically uses the language of the Home Assistant Assist
request. The 2026 top ten by total speakers are supported: English, Mandarin
Chinese, Hindi, Spanish, Modern Standard Arabic, French, Bengali, Portuguese,
Indonesian, and Urdu. Russian and German are included too, for **12 languages**.
If HA uses another language, assistant prompts and replies fall back to
English. The integration includes matching UI translations; the STT and TTS
engines selected in an Assist pipeline must also support that language.

## Install

The Home Assistant integration and the Laya model server are separate parts.
HACS manages the integration; the optional Laya Server app (formerly add-on)
downloads the model and runs it on HA OS or Supervised installations. Home
Assistant Container users can use the included Compose file or an existing
compatible Laya server. HACS cannot start containers on the HA host.

### Home Assistant OS or Supervised

1. Add `https://github.com/ps1x/LayaAssitant` to the **App Store → Repositories**.
2. Install **Laya Server**. The first start downloads the multilingual model.
   Wait for the server-ready line in its log. Set an API key if you expose port
   8000 beyond your trusted LAN.
3. In HACS, add the same URL as a custom **Integration** repository and install
   **Laya Assistant**. Restart Home Assistant.
4. In **Settings → Devices & services → Add integration**, choose **Laya
   Assistant**. Enter `http://<HA-host-address>:8000` and the matching API key.
   Select the exact entities Laya Assistant may control or read.
5. In **Settings → Voice assistants**, create or edit an Assist pipeline and
   choose **Laya Assistant** as its conversation agent. Select any STT and TTS
   engines you prefer. They are independent of this integration.

### Home Assistant Container

Clone this repository, then run `docker compose up -d --build` in the repo root.
Its model cache persists in `./laya-data`. The sample Compose file publishes
Laya on the host loopback interface; a Home Assistant container on a separate
Docker network cannot reach the host's `127.0.0.1`. Put both services on one
Docker network and use `http://laya:8000`, or publish Laya on a trusted LAN
interface and use the host address in the integration setup.

The server uses the Apache-2.0 licensed `laya` package. It needs a CPU with
several GB of free memory and storage; the model download and PyTorch image
make the first start slower than later starts. The add-on supports `amd64` and
`aarch64`. The HACS integration itself has no PyTorch dependency.

## Safety and behavior

- Control and read targets are chosen from the explicit allowlist in the config
  flow. Names and areas are read from HA's live registries for each request.
- The normal gate requires model confidence and selected probability of at
  least 0.80. For an explicit light command, a hesitant domain choice can pass
  at 0.60/0.80. A room-light target can pass at 0.65/0.90 only when two Laya
  target questions agree and the spoken room matches the approved HA area; a
  named fixture can pass at 0.75/0.90 only when its name and area match the
  request. The action still requires 0.80/0.80. Unavailable entities, unlisted
  targets, ambiguous rooms, and contradictory action words are rejected before
  a service call.
- Control and read permissions are checked against the HA user in the request
  context. Requests without an HA user ID cannot control or read entities.
- An area-light group contains only entities selected in **Lights**. Whole-home
  light control requires an explicit whole-home phrase and uses only selected
  lights.
- `sent` means HA accepted the service call. It does not prove that a physical
  lamp changed state.
- For uncommon area names or inflected forms, use **Spoken names** in the
  integration options. It accepts JSON such as
  `{"ru":{"area:Детская":"свет в детской","switch.kids_top":"верхний свет в детской"}}`.
  An `area:<HA area name>` key changes only the model's spoken description of
  that light group; an entity ID changes only its spoken description. Entity
  IDs and permissions never come from this text.
- The configured Laya endpoint receives recognized text and descriptions of
  allowed targets. Use a Laya server you trust. Laya's model may download from
  Hugging Face on first start; inference after that is local.

The entity exposes `domain_ms`, `target_ms`, `detail_ms`, `api_ms`, and
`total_ms` attributes to help diagnose latency. A stage skipped after an early
rejection has no timing attribute.

In a no-service-call check using a sample two-room catalog, 19 of 20 Russian
children's-room phrases produced the expected target and action. One request
(`погаси свет в детской`) was rejected at the action gate. One sample command
per supported language also reached the expected target and action. These are
smoke checks, not a measured accuracy benchmark or a physical light test.

## Development

Run `python3 -m unittest discover -s tests` for pure routing checks. HACS
repository metadata is in `hacs.json`; the optional app definition is in
`addon/laya/`. The canonical package lives under
`custom_components/laya_assistant/`.

This is an independent integration. Installing it does not replace an existing
conversation agent or change a preferred Assist pipeline.
