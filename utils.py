
import os
import mg_server # register components
from mg_server.morphable_graph_state_machine import DEFAULT_CONFIG

SERVER_TYPE_MAP = dict()
SERVER_TYPE_MAP["tcp"] = "animation_websocket_server"
SERVER_TYPE_MAP["websocket"] = "animation_server"


DATA_DIR = r".\data"
IN_CONFIG = dict()

def setup_scene(app, model_path, port=8888, in_config=IN_CONFIG, visualize=False):
    config = DEFAULT_CONFIG
    config.update(in_config)

    if "n_tree_search_candidates" in config:
        config["algorithm"]["n_cluster_search_candidates"] = config["n_tree_search_candidates"]
    use_all_joints = False
    if "use_all_joints" in config:
        use_all_joints = config["use_all_joints"]

    server_type = SERVER_TYPE_MAP["tcp"]
    if "connection_type" in config:
        connection_type = config["connection_type"]
        if connection_type in SERVER_TYPE_MAP:
            server_type = SERVER_TYPE_MAP[connection_type]
    if os.path.isfile(model_path):
        o = app.scene.object_builder.create_object_from_file("mg.zip", model_path, use_all_joints=use_all_joints, config=config)
    else:
        o = app.scene.object_builder.create_object("mg_from_db",model_path, use_all_joints=use_all_joints, config=config)
    
    if o is None or "morphablegraph_state_machine" not in o._components:
        print("Error: Could not load model", model_path)
        return
    
    c = o._components["morphablegraph_state_machine"]
    c.show_skeleton = visualize
    c.activate_emit = False

    server = app.scene.object_builder.create_component(server_type, o, "morphablegraph_state_machine", port)
    o.name = "morphablegraph_state_machine"+str(port)
    if "search_for_message_header" in config:
        server.search_message_header = config["search_for_message_header"]

    c.update_transformation()
    o._components["animation_server"].start()
    if "scene_interface_port" in config:
        o = app.scene.object_builder.create_object("scene_interface", config["scene_interface_port"])
        o._components["scene_interface"].start()
    return c
