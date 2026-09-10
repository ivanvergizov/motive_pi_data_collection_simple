# Motive + SDR Simple Data Collection

This project supports two command-line programs:

1. simple live Motive/SDR acquisition using `run_sdr_motive.py`,
2. a single-frame NatNet diagnostic.

The sections below describe how to use both programs, the network communication they rely on, and the files that implement them.

## Single-frame NatNet check

For the quickest Motive/NatNet connectivity test, run the included single-frame utility:

```powershell
py motive_data_collection_single_frame/single_frame.py -s <SERVER_IP> -c <CONTROLLER_IP>
```

Example:

```powershell
py motive_data_collection_single_frame/single_frame.py -s 10.1.1.51 -c 10.1.1.52
```

`-s` is the IP address of the computer running Motive/NatNet. `-c` is the local IP address of the computer running the script on the NatNet network. Unicast is used by default. Add `-m` for multicast.

The program performs the NatNet connection handshake, waits for one rigid-body frame, prints the frame number, rigid-body IDs, tracking-valid values, positions, and quaternions, then exits.

## Simple live acquisition usage

### Install dependencies

Windows:

```powershell
py -m pip install -r requirements.txt
```

Linux:

```bash
python3 -m pip install -r requirements.txt
```

### Start live acquisition

At least one source must be selected explicitly.

SDR only:

```powershell
py run_sdr_motive.py --sdr
```

Motive only:

```powershell
py run_sdr_motive.py --motive
```

SDR and Motive together:

```powershell
py run_sdr_motive.py --sdr --motive
```

By default the program loads its network and recording values from `testbed.json`. Command-line flags can override those values for the current run.

### Main flags

```text
--config PATH                 override the default testbed.json path
--sdr                         run the configured SDR receivers
--motive                      run the Motive/NatNet receiver
--motive-multicast            override Motive transport to multicast
--motive-unicast              override Motive transport to unicast
--output-directory PATH       override controller.output_directory
--duration SECONDS            stop after the specified duration; 0 runs until Ctrl+C
--name NAME                   recording/run name
--no-record                   run without writing CSV files
--motive-recording-rate RATE  override motive.recording_rate_hz
--sdr-recording-rate RATE     override sdr.recording_rate_hz
--motive-interface-ip IP      override motive.interface_ip
--motive-server-ip IP         override motive.server_ip
--status-interval SECONDS     set how often status is printed
```

### Motive-only example with explicit addresses

```powershell
py run_sdr_motive.py --motive --motive-unicast --motive-server-ip 10.1.1.51 --motive-interface-ip 10.1.1.52
```

### SDR-only example

```powershell
py run_sdr_motive.py --sdr --sdr-recording-rate 10
```

### Combined timed recording

```powershell
py run_sdr_motive.py --sdr --motive --duration 30 --name test_run
```

### Run without recording

```powershell
py run_sdr_motive.py --sdr --motive --no-record
```

### Status output

While running, the command-line program prints current source status. SDR status reports the configured receivers and their latest state/value. Motive status reports whether the client is waiting or shows the newest received frame information.

Stop an indefinite run with `Ctrl+C`.

## Single-frame command-line inputs

The single-frame utility does not use `testbed.json`. All required network inputs are provided as flags.

Show help:

```powershell
py motive_data_collection_single_frame/single_frame.py --help
```

Required flags:

```text
-s, --server-ip IP       NatNet server IP
-c, --controller-ip IP   local IPv4 address of this computer on the NatNet network
```

Optional flags:

```text
-m, --multicast          use multicast; unicast is the default
-t, --timeout SECONDS    frame wait timeout; default 5 seconds
--command-port PORT      NatNet command port; default 1510
--data-port PORT         NatNet data port; default 1511
--multicast-group IP     NatNet multicast group; default 239.255.42.99
```

Unicast example:

```powershell
py motive_data_collection_single_frame/single_frame.py -s 10.1.1.51 -c 10.1.1.52
```

Multicast example:

```powershell
py motive_data_collection_single_frame/single_frame.py -s 10.1.1.51 -c 10.1.1.52 -m
```

Longer frame timeout:

```powershell
py motive_data_collection_single_frame/single_frame.py -s 10.1.1.51 -c 10.1.1.52 -t 15
```

After a successful handshake, the program prints the reported NatNet and Motive versions, waits for the first rigid-body frame, prints the frame contents, and exits.

Example output format:

```text
Connecting to 10.1.1.51:1510 from 10.1.1.52 using unicast...
Handshake succeeded. NatNet=..., Motive=...
Waiting up to 5 seconds for one frame...

Frame number: 12345
Rigid bodies: 2

Rigid Body 1
  ID: 1
  Tracking valid: True
  Position: X=1.234000, Y=0.456000, Z=2.100000
  Quaternion: X=0.000000, Y=0.000000, Z=0.000000, W=1.000000
```

## `testbed.json` inputs

`run_sdr_motive.py` uses `testbed.json` for its default live configuration.

```json
{
  "controller": {
    "output_directory": "live_csv_output"
  },
  "sdr": {
    "enabled": true,
    "recording_rate_hz": 10.0,
    "receivers": [
      {"node": 165, "host": "10.1.1.165", "port": 55555},
      {"node": 166, "host": "10.1.1.166", "port": 55555}
    ]
  },
  "motive": {
    "enabled": true,
    "server_ip": "10.1.1.51",
    "interface_ip": "10.1.1.52",
    "use_multicast": false,
    "recording_rate_hz": null
  }
}
```

Main values:

- `controller.output_directory` — parent directory for live recordings.
- `sdr.recording_rate_hz` — controller SDR snapshot/recording rate.
- `sdr.receivers[].node` — receiver identity and SDR CSV column identity.
- `sdr.receivers[].host` — receiver's ZeroMQ host/IP.
- `sdr.receivers[].port` — receiver's ZeroMQ TCP port.
- `motive.server_ip` — Motive/NatNet server address.
- `motive.interface_ip` — local interface used for NatNet traffic.
- `motive.use_multicast` — `false` for unicast or `true` for multicast.
- `motive.recording_rate_hz` — Motive CSV recording-rate limit; `null` records every received frame.

The `--sdr` and `--motive` command-line flags determine which sources actually run. The enabled values in the JSON do not replace those source-selection flags for `run_sdr_motive.py`.

## Network structure and communication

### Motive / NatNet

The computer running the simple program acts as the NatNet client. The computer running Motive acts as the NatNet server.

```text
Controller / client                         Motive / server
motive.interface_ip                         motive.server_ip
        |                                          |
        |------ NatNet command traffic ---------->| UDP 1510
        |<----- server/command responses ----------|
        |                                          |
        |<----- NatNet frame data -----------------|
```

The default NatNet command port is UDP `1510`. The default NatNet data port is UDP `1511`.

At startup, the NatNet client sends a connection request and waits for server information. The live Motive receiver obtains model definitions so rigid-body IDs can be associated with body names, then processes incoming frame data.

Each rigid body includes:

- rigid-body ID
- body name when model definitions are available
- X/Y/Z position
- quaternion X/Y/Z/W
- tracking-valid state

The controller timestamps received Motive frames.

#### Unicast

With unicast selected, the local controller interface is identified by `motive.interface_ip`, and the NatNet server is identified by `motive.server_ip`.

#### Multicast

With multicast selected, the controller joins the NatNet multicast group `239.255.42.99` using `motive.interface_ip` as the local interface.

### Single-frame NatNet communication

The single-frame utility uses the same server/client address roles but does not use the live acquisition session or recorder.

```text
single_frame.py
     |
     | NAT_CONNECT / UDP command traffic
     v
NatNet server
     |
     | server information
     v
single_frame.py
     |
     | first rigid-body frame
     v
print frame and exit
```

It prints the first received frame and exits without writing a CSV file.

### SDR / GNU Radio

Each configured SDR receiver publishes measurements through its own ZeroMQ TCP endpoint.

```text
Receiver 165 / GNU Radio ---- TCP/ZMQ ----\
                                         \
Receiver 166 / GNU Radio ---- TCP/ZMQ -----> Controller
                                         /
Receiver N / GNU Radio ------ TCP/ZMQ ----/
```

The controller creates one ZeroMQ SUB socket for each receiver. Each socket is associated with that receiver's configured node number.

The newest ZMQ message is decoded as `float32` values. All values in that message are averaged, and that average becomes the receiver's latest power measurement.

The latest measurement is retained separately for each node. `sdr.recording_rate_hz` determines how often the controller snapshots the current values into a recording row. It does not control how quickly GNU Radio publishes messages.

### Recording

`LiveAcquisitionSession` coordinates the active receivers and `CsvSessionRecorder`.

```text
SDR ZMQ receivers ----\
                       >---- LiveAcquisitionSession ---- CsvSessionRecorder ---- CSV files
Motive NatNet --------/
```

When recording is enabled, the output directory can contain:

```text
sdr_samples.csv
motive_rigid_bodies.csv
```

SDR CSV rows use controller snapshot timing. Motive CSV rows use controller receive timing. Both use elapsed decimal seconds in their recorded time columns.

## Project folders, files, and main functions

A simple non-GUI project needs only the live acquisition code, configuration, command-line runner, and the included single-frame diagnostic.

```text
motive_data_collection_simple/
├── README.md
├── requirements.txt
├── run_sdr_motive.py
├── testbed.json
├── testbed.schema.json
├── motion_app/
│   └── live/
│       ├── __init__.py
│       ├── acquisition_session.py
│       ├── motive_receiver.py
│       ├── natnet_client.py
│       ├── recording.py
│       ├── sdr_receiver.py
│       └── testbed.py
└── motive_data_collection_single_frame/
    ├── README.md
    ├── requirements.txt
    ├── single_frame.py
    └── natnet_client.py
```

### Top-level files

- `run_sdr_motive.py` — command-line live acquisition entry point.
  - defines the CLI flags,
  - loads `testbed.json`,
  - applies temporary command-line overrides,
  - selects SDR, Motive, or both,
  - starts `LiveAcquisitionSession`,
  - prints source status,
  - stops the session on timeout or `Ctrl+C`.
- `testbed.json` — default Motive, SDR, and recording settings.
- `testbed.schema.json` — schema describing valid configuration fields.
- `requirements.txt` — Python dependencies for the live command-line program.

### `motion_app/live/`

- `testbed.py` — configuration classes, parsing, validation, and overrides.
  - `load_testbed()` reads configuration.
  - `override_testbed()` applies current-run overrides.
  - `save_testbed()` writes configuration when needed by code using this module.
- `natnet_client.py` — NatNet UDP communication and packet parsing.
  - creates NatNet sockets,
  - sends the connection request,
  - receives server information,
  - obtains model definitions,
  - parses rigid-body frame packets.
- `motive_receiver.py` — higher-level Motive receiver.
  - associates rigid-body IDs with names,
  - timestamps complete frames,
  - retains the newest frame,
  - passes frames to the recorder callback.
- `sdr_receiver.py` — SDR ZeroMQ receiver manager.
  - creates one SUB socket per configured receiver,
  - receives newest ZMQ messages,
  - averages each message's `float32` values,
  - retains the latest value per receiver,
  - creates snapshots at `sdr.recording_rate_hz`.
- `acquisition_session.py` — shared session coordinator.
  - `start()` starts the recorder and requested data sources.
  - `stop()` stops the Motive/SDR receivers and recorder.
  - latest-value methods expose current source information to the command-line runner.
- `recording.py` — background CSV recording.
  - writes SDR snapshots,
  - writes Motive rigid-body frames,
  - manages output files and final shutdown.

### `motive_data_collection_single_frame/`

- `single_frame.py` — one-frame CLI program.
  - `ipv4()` validates IPv4 inputs.
  - `port()` validates UDP ports.
  - `build_parser()` defines command-line inputs.
  - `main()` connects, waits for one frame, prints it, and exits.
- `natnet_client.py` — minimal NatNet transport/parser used only by the one-frame utility.
  - `NatNetSingleFrameClient.start()` creates sockets and performs the handshake.
  - `stop()` closes sockets and the receive thread.
  - `_send_connect()` sends the NatNet connection request.
  - `_send_keepalive()` maintains the unicast command connection while waiting.
  - `_receive_loop()` receives UDP packets.
  - `_process_packet()` dispatches supported packets.
  - `_parse_server_info()` parses server/NatNet version information.
  - `_parse_frame()` extracts the rigid-body section of a frame.
- `requirements.txt` — dependency information for the standalone one-frame program.
