from pathlib import Path
import json, yaml
import pprint

facebook_data_dir = Path(__file__).joinpath("..").resolve()

for file_name in {"event_data", "message_data", "messaging_data", "response_message_data"}:
    json_data = None
    with open(f"{facebook_data_dir}/{file_name}.json") as rfile:
        json_data = json.load(rfile)
    
    yaml_str = yaml.safe_dump(json_data, default_flow_style=False, width=100, allow_unicode=True)
    print(yaml_str)
    print("\n")
    with open(f"{facebook_data_dir}/{file_name}.yaml", "w") as wfile:
        yaml.dump(pprint.pformat(yaml_str), wfile, default_flow_style=False, width=100, allow_unicode=True)