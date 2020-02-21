import os
import argparse
from multiprocessing import Process
import vis_utils.constants as constants
constants.activate_simulation = False
from utils import setup_scene
from vis_utils.glut_app import GLUTApp
from vis_utils.scene.task_manager import Task
from vis_utils.io import load_json_file


def print_global_vars(dt, app):
    scene = app.scene
    lines = []
    for key in scene.global_vars:
        value = str(scene.global_vars[key])
        lines.append(key+": "+value)
    app.console.set_lines(lines)


def control_func(key, params):
    app, controller = params
    controller.handle_keyboard_input(bytes.decode(key, "utf-8"))
    if key == b"t":
        if app.get_camera()._target is None:
            app.set_camera_target(controller)
        else:
            app.set_camera_target(None)

IN_CONFIG = dict()


def start_app(file_path, port=8888, config=IN_CONFIG):
    console_scale = 0.4
    camera_pose = dict()
    camera_pose["zoom"] = -500
    camera_pose["position"] = [0, 0, -50]
    camera_pose["angles"] = (45, 200)
    a = GLUTApp(800, 600, title="server "+str(port),console_scale=console_scale, camera_pose=camera_pose)

    controller = setup_scene(a, file_path, port, config, visualize=True)
    if controller is not None:
        a.set_camera_target(controller)
        a.keyboard_handler["anim_control"] = control_func, (a, controller)
        a.scene.draw_task_manager.add("print", Task("print", print_global_vars, a))
        print("Press WASD to control the walk direction")
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
        port+=1

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