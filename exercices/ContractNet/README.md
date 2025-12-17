# ContractNet – Distributed Task Allocation with MQTT

This exercise implements the Contract Net Protocol (CNP) using MQTT as a
communication middleware. The goal is to demonstrate distributed task allocation
between autonomous agents without direct coupling.

---

## 1. Objective

The objective of this exercise is to implement the classical Contract Net Protocol:
- a **supervisor agent** announces tasks,
- **machine agents** evaluate tasks and submit proposals,
- the supervisor selects the best proposal and assigns the task.

All interactions are performed asynchronously through MQTT topics.

---

## 2. Agents Overview

### 2.1 Supervisor Agent

The supervisor agent is responsible for:
- publishing Calls for Proposals (CfP),
- collecting proposals from machine agents,
- selecting the best proposal according to a cost criterion,
- notifying agents of acceptance or rejection.

The supervisor does not know the internal state of machines and relies solely
on proposals received via MQTT.

### 2.2 Machine Agents

Each machine agent:
- subscribes to Calls for Proposals,
- evaluates whether it can perform the task,
- sends a proposal containing its estimated execution time,
- executes the task if selected by the supervisor.

Machine agents operate autonomously and independently from each other.

---

## 3. MQTT Topics and Messages

The following MQTT topics are used:

| Purpose | Topic |
|------|------|
| Call for Proposals | `contractnet/cfp` |
| Proposals | `contractnet/proposal` |
| Accept proposal | `contractnet/accept/<machine_id>` |
| Reject proposal | `contractnet/reject/<machine_id>` |
| Task completion | `contractnet/done` |

All messages are serialized using JSON.

### Example: Call for Proposals

```json
{
  "job": {
    "id": "job_1",
    "name": "Task A"
  }
}

from the root of the repository:
```
cd ~/Documents_distants/Mqtt_Lab_DORBEZ_OUNI
python -m exercices.ContractNet.exemples.run_contractnet
```