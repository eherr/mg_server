import os
from .morphable_graph_state_machine import MorphableGraphStateMachine, DEFAULT_CONFIG, MotionStateGraphLoader
from .simple_navigation_agent import SimpleNavigationAgent
from .animation_tcp_server import AnimationTCPServerComponent
from .animation_websocket_server import AnimationWebSocketServerComponent
from .collision_boundary import CollisionBoundaryComponent
from .hand_collision_boundary import HandCollisionBoundaryComponent
from vis_utils.scene.scene_object_builder import SceneObjectBuilder, SceneObject
from vis_utils.scene.utils import get_random_color
from .scene_interface import SceneInterface
from morphablegraphs.utilities.db_interface import get_graph_list_from_db, download_graph_from_remote_db


def load_morphable_graph_state_machine(builder, path, use_all_joints=False, config=DEFAULT_CONFIG):
    scene_object = SceneObject()
    scene_object.scene = builder._scene
    builder.create_component("morphablegraph_state_machine", scene_object, path, use_all_joints, config)
    builder._scene.addObject(scene_object)
    return scene_object

def load_morphable_graph_state_machine_from_db(builder, model_url, use_all_joints=False, config=DEFAULT_CONFIG):
    scene_object = SceneObject()
    scene_object.scene = builder._scene
    builder.create_component("morphablegraph_state_machine_from_db", scene_object, model_url, use_all_joints, config)
    builder._scene.addObject(scene_object)
    return scene_object

def attach_mg_state_machine(builder, scene_object,file_path, use_all_joints=False, config=DEFAULT_CONFIG):
    color=get_random_color()  
    loader = MotionStateGraphLoader()
    loader.use_all_joints = use_all_joints# = set animated joints to all
    if os.path.isfile(file_path):
        loader.set_data_source(file_path[:-4])
        graph = loader.build()
        name = file_path.split("/")[-1]
        start_node = ("walk", "idle")
        animation_controller = MorphableGraphStateMachine(scene_object, graph, start_node, use_all_joints=use_all_joints, config=config, pfnn_data=loader.pfnn_data)
        scene_object.add_component("morphablegraph_state_machine", animation_controller)
        scene_object.name = name
        if builder._scene.visualize:
            vis = builder.create_component("skeleton_vis", scene_object, animation_controller.get_skeleton(), color)
            animation_controller.set_visualization(vis)
        agent = SimpleNavigationAgent(scene_object)
        scene_object.add_component("nav_agent", agent)
        return animation_controller

def attach_mg_state_machine_from_db(builder, scene_object, model_url, use_all_joints=False, config=DEFAULT_CONFIG):
    color=get_random_color()
    loader = MotionStateGraphLoader()
    loader.use_all_joints = use_all_joints# = set animated joints to all
    split_url = model_url.split("/graph/")
    if len(split_url) < 2:
        return
    db_url = split_url[0]
    split_name = split_url[1].split("/")
    if len(split_name) < 2:
        return
    skeleton_name = split_name[0]
    graph_name = split_name[1]
    print("try to load graph",skeleton_name,graph_name, "from db url", db_url,)
    graph_list = get_graph_list_from_db(db_url, skeleton_name)
    if graph_list is None:
        return
    graph_id = None
    print("found", len(graph_list), "graphs")
    for _id, _name in graph_list:
        if _name == graph_name:
            graph_id = _id
    if graph_id is not None:
        frame_time=1.0/72
        graph = loader.build_from_database(db_url, skeleton_name, graph_id, frame_time)
        start_node  = None
        name = skeleton_name
        animation_controller = MorphableGraphStateMachine(scene_object, graph, start_node, use_all_joints=use_all_joints, config=config, pfnn_data=loader.pfnn_data)
        scene_object.add_component("morphablegraph_state_machine", animation_controller)
        scene_object.name = name
        if builder._scene.visualize:
            vis = builder.create_component("skeleton_vis", scene_object, animation_controller.get_skeleton(), color)
            animation_controller.set_visualization(vis)
        agent = SimpleNavigationAgent(scene_object)
        scene_object.add_component("nav_agent", agent)
        return animation_controller


def attach_animation_server(builder, scene_object, src, port=8888):
    server = AnimationTCPServerComponent(port, scene_object, src)
    scene_object.add_component("animation_server", server)
    return server


def attach_animation_websocket_server(builder, scene_object, src, port=8888):
    server = AnimationWebSocketServerComponent(port, scene_object, src)
    scene_object.add_component("animation_server", server)
    return server

def attach_collision_boundary(builder, scene_object, radius,length, animation_src, visualize=True):
    boundary = CollisionBoundaryComponent(radius,length, animation_src, scene_object,visualize=visualize)
    scene_object.add_component("collision_boundary", boundary)
    return boundary

def attach_hand_collision_boundary(builder, joint_name, scene_object, radius, animation_src, visualize=True):
    boundary = HandCollisionBoundaryComponent(joint_name, radius, animation_src, scene_object,visualize=visualize)
    scene_object.add_component("collision_boundary", boundary)
    return boundary

def create_scene_rest_interface(builder, port):
    scene_object = SceneObject()
    builder._scene.addObject(scene_object)
    scene_rest_interface = SceneInterface(scene_object, port)
    scene_object.add_component("scene_interface", scene_rest_interface)
    return scene_object



SceneObjectBuilder.register_component("morphablegraph_state_machine", attach_mg_state_machine)
SceneObjectBuilder.register_component("morphablegraph_state_machine_from_db", attach_mg_state_machine_from_db)
SceneObjectBuilder.register_component("animation_server", attach_animation_server)
SceneObjectBuilder.register_component("animation_websocket_server", attach_animation_websocket_server)
SceneObjectBuilder.register_component("collision_boundary", attach_collision_boundary)
SceneObjectBuilder.register_component("hand_collision_boundary", attach_hand_collision_boundary)
SceneObjectBuilder.register_object("mg_from_db", load_morphable_graph_state_machine_from_db)
SceneObjectBuilder.register_object("scene_interface", create_scene_rest_interface)
SceneObjectBuilder.register_file_handler("mg.zip", load_morphable_graph_state_machine)
