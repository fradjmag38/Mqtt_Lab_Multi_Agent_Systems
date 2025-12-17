# ContractNet

Supervisor and Machine agents implementing a Contract Net Protocol over MQTT.

Run the demo single-process:
cd ~/Documents_distants/Mqtt_Lab_DORBEZ_OUNI
python -m exercices.ContractNet.exemples.run_contractnet   # comme etant un module python

Topics:
- CfP: contractnet/cfp
- Proposals: contractnet/proposal
- Accept: contractnet/accept/{machine_id}
- Reject: contractnet/reject/{machine_id}
- Done: contractnet/done
