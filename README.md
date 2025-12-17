
# MQTT Lab – Multi-Agent Systems

This repository contains a complete and modular Python implementation of the MQTT
laboratory for Multi-Agent Systems.

The project covers three exercises:
- **FirstContact**: basic MQTT connectivity (publish / subscribe).
- **SensorNetwork**: smart-home simulation with room-level orchestration, sensors,
  aggregation and anomaly detection.
- **ContractNet**: distributed task allocation using the Contract Net Protocol.

The implementation follows clean software engineering principles, strict modularity,
and is fully documented in English.

---

## 1. Requirements

### 1.1 Software Requirements

- **Python**: 3.9 or newer (tested with Python 3.10+)
- **MQTT Broker**: 

#### Python dependencies
All Python dependencies are listed in `requirements.txt`:
```text
paho-mqtt>=1.6.1
sphinx>=6.0
pytest>=7.0
````

Install them using:

```bash
pip install -r requirements.txt
```

The default broker used by all scripts is:

```
host: localhost
port: 1883
```

---

## 2. Project Structure and Architecture

### 2.1 Repository Tree

```
mqtt_lab/
├─ README.md
├─ requirements.txt
├─ setup.cfg
├─ docs/                      # Sphinx documentation (English)
│  ├─ conf.py
│  ├─ index.rst
│  └─ make.bat
├─ exercices/
│  ├─ FirstContact/
│  │  ├─ client.py
│  │  ├─ start_clients.sh
│  │  └─ README.md
│  ├─ SensorNetwork/
│  │  ├─ mqtt_client.py
│  │  ├─ simulation.py
│  │  ├─ README.md
│  │  ├─ exemples/
│  │  │  ├─ run_simulation.py
│  │  │  ├─ publish_control.py
│  │  │  └─ README.md
│  │  └─ agents/
│  │     ├─ base_agent.py
│  │     ├─ sensor_factory.py
│  │     ├─ room_agent.py
│  │     ├─ averaging_agent.py
│  │     ├─ detection_agent.py
│  │     └─ interface_agent.py
│  └─ ContractNet/
│     ├─ mqtt_client.py
│     ├─ supervisor.py
│     ├─ machine_agent.py
│     ├─ exemples/
│     │  ├─ run_contractnet.py
│     │  └─ README.md
│     └─ README.md
└─ report/
   └─ report.pdf
```

---

## 3. Global Design Principles

* **Loose coupling**: all interactions are done through MQTT topics.
* **Clear agent responsibilities**: each agent has a single, well-defined role.
* **Hierarchical organization**:

  * RoomAgent orchestrates sensors and actuators.
  * Sensors remain autonomous.
* **Thread-based concurrency**: one thread per active agent when required.
* **JSON serialization**: human-readable, lightweight, and sufficient for the lab.

---

## 4. Exercise 1 – FirstContact

### 4.1 Objective

Verify basic MQTT connectivity by implementing simple clients capable of publishing
and subscribing to messages.

### 4.2 Execution

Open two terminals.

**Terminal 1 (pong):**

```bash
cd exercices/FirstContact
python client.py --role pong
```

**Terminal 2 (ping):**

```bash
cd exercices/FirstContact
python client.py --role ping
```
Or you can run the shel scripte to execute the publisher and subscriber
```bash
./start_clients
```

### 4.3 Observed Behavior

* The `ping` client publishes messages.
* The `pong` client subscribes and reacts.
* Successful exchanges validate broker configuration and topic usage.

---

## 5. Exercise 2 – SensorNetwork (Smart Home)

### 5.1 Architecture Overview

This exercise implements a smart-home simulation using multiple interacting agents.

#### Main agent types:

* **RoomAgent**: manages sensors and actuators (heating, window).
* **SensorAgent**: publishes simulated measurements.
* **AveragingAgent**: computes rolling averages per room/measurement.
* **DetectionAgent**: detects abnormal values and publishes alerts.
* **InterfaceAgent**: logs averages and alerts for human monitoring.

### 5.2 MQTT Topics

| Purpose     | Topic                                   |
| ----------- | --------------------------------------- |
| Sensor data | `home/<room>/<measurement>/<sensor_id>` |
| Averages    | `home/<room>/<measurement>/average`     |
| Alerts      | `home/alerts/<room>`                    |
| Control     | `home/<room>/control/#`                 |

All payloads are JSON encoded.

### 5.3 Execution

Start the simulation:

```bash
cd exercices/SensorNetwork
python simulation.py
```

Alternatively:

```bash
python exemples/run_simulation.py
```

### 5.4 Dynamic Control (Optional)

From another terminal, send control commands:

```bash
cd exercices/SensorNetwork/exemples
python publish_control.py --room bedroom1 --command heating --value true
python publish_control.py --room bedroom1 --command window --value true
python publish_control.py --room bedroom1 --command add_sensor \
    --measurement temperature --sensor_id bedroom1_temp_03 --baseline 22.0
```

Changes are applied at runtime without restarting the simulation.

---

## 6. Exercise 3 – ContractNet

### 6.1 Objective

Implement a distributed task allocation mechanism using the Contract Net Protocol.

### 6.2 Agents

* **Supervisor**:

  * Issues Calls for Proposals (CfP)
  * Selects the best proposal
* **MachineAgent**:

  * Evaluates CfPs
  * Submits proposals
  * Executes accepted tasks

### 6.3 MQTT Topics

| Purpose    | Topic                             |
| ---------- | --------------------------------- |
| CfP        | `contractnet/cfp`                 |
| Proposals  | `contractnet/proposal`            |
| Accept     | `contractnet/accept/<machine_id>` |
| Reject     | `contractnet/reject/<machine_id>` |
| Completion | `contractnet/done`                |

### 6.4 Execution

Run the Contract Net demo:

```bash
cd ~/Documents_distants/Mqtt_Lab_DORBEZ_OUNI
python -m exercices.ContractNet.exemples.run_contractnet
```

---

## 7. Documentation (Sphinx)

The project is fully documented using Sphinx.

Generate the HTML documentation:

```bash
cd docs
make html
```

Output will be available in:

```
docs/_build/html/index.html
```

---

## 8. Report

The final report is available in PDF format:

```
report/MQTT_Lab_DORBEZ_OUNI.pdf
```

It presents:

* technical choices,
* execution traces,
* code highlights,
* encountered difficulties and solutions.

---

## 9. Notes

* All identifiers, logs, and documentation are written in English.
* The project is designed to be easily extensible.
* Agents can be executed in separate processes for more realistic simulations.

---

## 10. License

This project is provided for educational purposes for the cs534 lesson.


