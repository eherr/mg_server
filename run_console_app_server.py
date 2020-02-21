import os
import argparse
from multiprocessing import Process
import vis_utils.constants as constants
constants.activate_simulation = False
from vis_utils.console_app import ConsoleApp
from utils import setup_scene
from vis_utils.io import load_json_file

IN_CONFIG = dict()

def start_app(file_path, port=8888, config=IN_CONFIG):
    sync_sim = False
    a = ConsoleApp(fps=60.0, sync_sim=sync_sim)
    controller = setup_scene(a, file_path, port, config, visualize=False)
    if controller is not None:
        a.run()

def start_server_processes(config):
    port = config["port"]
    n_agents = config["n_agents"]
    model_path = config["model_path"]
    processes = []
    for n in range(n_agents):
        p = Process(target=start_app, args=(model_path, port, config))
        processes.append(p)
        p.start()
        port += 1
        if "scene_interface_port" in config:
            config["scene_interface_port"] += 1

    for p in processes:
        p.join()


CONFIG_FILE = "config.json"
def main():
    config = load_json_file(CONFIG_FILE)
    parser = argparse.ArgumentParser(description='Start to server.')
    parser.add_argument('model_path', nargs='?', default=None, help='Path to model file or server url')
    parser.add_argument('port', nargs='?', default=None, help='Port')
    args = parser.parse_args()
    if args.model_path is not None:
        print("set model path to", args.model_path)
        config["model_path"] = args.model_path
    if args.port is not None:
        print("set port to", args.port)
        config["port"] = int(args.port)
    start_server_processes(config)

if __name__ == "__main__":
    main()
