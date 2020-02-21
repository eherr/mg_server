import numpy as np
import json
from vis_utils.scene.components import ComponentBase
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import asyncio
import threading
import time
from .animation_tcp_server import to_unity_frame, parse_client_message, STANDARD_DT


class ServerThread(threading.Thread):
    """ Controls a WebSocketApplication by starting a tornado IOLoop instance
    """
    def __init__(self, web_app, port=8889):
        threading.Thread.__init__(self)
        self.web_app = web_app
        self.port = port

    def run(self):
        print("starting web socket server on port", self.port)
        asyncio.set_event_loop(asyncio.new_event_loop())
        #self.web_app.listen(self.port)
        self.web_app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def stop(self):
        print("stopping server")
        tornado.ioloop.IOLoop.instance().stop()


class BroadcastThread(threading.Thread):
    """ Controls a WebSocketApplication by starting a tornado IOLoop instance
    """
    def __init__(self, web_app):
        threading.Thread.__init__(self)
        self.web_app = web_app

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        while True:
            try:
                frame = self.web_app.server.get_frame()
                if frame is not None:
                    server_msg = json.dumps(frame)
                    server_msg = server_msg.encode("utf-8")
                    #self.web_app.send_message(server_msg)
                time.sleep(self.web_app.server.get_frame_time())
            except Exception as e:
                print("Error: ", e.args)
                return


class AnimationWebSocketHandler(tornado.websocket.WebSocketHandler):
        """ extends the websocket.WebSocketHandler class to implement open, on_message,on_close
        additionally it adds itself to the list of connections of the web application
        """
        def __init__(self, application, request, **kwargs):
            tornado.websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
            self.id = -1
            self.app = application

        def set_default_headers(self):
            print("setting headers!!!")
            self.set_header("Access-Control-Allow-Origin", "*")

        def open(self):
            """ add the new connection to then connection list of the class that controls the animation engine thread
            """
            print("WebSocket opened")
            self.id = self.app.addConnection(self)

        def on_message(self, message):
            message = bytes.decode(message, "utf-8")
            parse_client_message(self.app.server, message)
            #return
            server_msg = "Empty"
            if message.startswith("SetPose"):
                skel_dict = self.app.server.get_skeleton_dict()
                server_msg = "Skeleton:"+json.dumps(skel_dict)
                server_msg = server_msg.encode("utf-8")
                print("send skeleton")
            else:
                frame = self.app.server.get_frame()
                if frame is not None:
                    server_msg = "Pose:"+json.dumps(frame)
                    server_msg = server_msg.encode("utf-8")
            #print(server_msg)
            self.app.send_message(server_msg)

        def on_close(self):
            print("WebSocket closed")
            self.app.removeConnection(self.id)

        def check_origin(self, origin):
            print("check origin",origin)
            return True



class WebSocketApplication(tornado.web.Application):
    """ extends the Application class by a list of connections to allow access from other classes
    """
    def __init__(self, server, handlers=None, default_host="", transforms=None, **settings):
        self.server = server
        tornado.web.Application.__init__(self, handlers, default_host, transforms)
        self.connections = {}
        self.activateBroadcast = False

        self.idCounter = 0

    def addConnection(self, connection):
        """
        is called by the AnimationWebSocketHandler instance of a new connection
        """
        id = self.idCounter
        self.idCounter += 1
        self.connections[id] = connection
        return id

    def removeConnection(self,id):
        """
        is called by the AnimationWebSocketHandler instance before its destruction
        """
        del self.connections[id]
        print("removed the connection")

    def sendDataToId(self, id, data):
        """
        @param message dictionary that is supposed to be send to one websocket client
        send message formated as a dictionary via JSON to all connections. Not efficient but normally only one connection is supposed to be established with another server
        """
        json_data = json.dumps(data)
        if id in self.connections.keys():
            self.connections[id].write_message(json_data)
        return

    def sendData(self, data):
        """
        @param message dictionary that is supposed to be send to the websocket clients
        send message formated as a dictionary via JSON to all connections. Not efficient but normally only one connection is supposed to be established with another server
        """
        print("sending data to ",len(self.connections)," clients")
        json_data = json.dumps(data)
        for id in self.connections.keys():
            self.connections[id].write_message(json_data)

    def send_message(self, msg):
        """
        @param message dictionary that is supposed to be send to the websocket clients
        send message formated as a dictionary via JSON to all connections. Not efficient but normally only one connection is supposed to be established with another server
        """
        for id in self.connections.keys():
            self.connections[id].write_message(msg)

    def toggleActiveBroadcast(self):
        self.activateBroadcast = not self.activateBroadcast
        if self.activateBroadcast:
            print("activated broadcast")
        else:
            print("deactivated broadcast")


class AnimationWebSocketServerComponent(ComponentBase):
    def __init__(self, port, scene_object, src_component):
        print("create animation server", port)
        ComponentBase.__init__(self, scene_object)
        web_app = WebSocketApplication(self, [(r"/ws", AnimationWebSocketHandler)])
        self.server_thread = ServerThread(web_app, port)
        self.broadcast_thread = BroadcastThread(web_app)
        self.src_component_key = src_component
        self.animation_src = scene_object._components[src_component]
        self.animation_src.animation_server = self
        self.activate_emit = True
        self.frame_buffer = None
        self.skeleton = self.animation_src.get_skeleton()
        self.animated_joints = [key for key in self.skeleton.nodes.keys() if len(self.skeleton.nodes[key].children) >0]#self.skeleton.animated_joints# self.animation_src.get_animated_joints()
        self.scale = 1.0

    def start(self):
        self.server_thread.start()
        #self.broadcast_thread.start()
        print("started server")

    def stop(self):
        self.server_thread.stop()

    def update(self, dt):
        frame = self.animation_src.get_current_frame()
        action = ""
        events = list()
        is_idle = True
        if self.src_component_key == "morphablegraph_state_machine":
            action = self.animation_src.current_node[1]
            events = self.animation_src.get_events()
            is_idle = len(self.animation_src.planner.state_queue) == 0 and not self.animation_src.planner.is_processing
        self.frame_buffer = to_unity_frame(self.skeleton, frame, self.animated_joints, self.scale, action, events, is_idle)
        #self.animation_src.handle_keyboard_input(self.input_key)
        

    def get_frame(self):
        return self.frame_buffer

    def get_frame_time(self):
        return self.animation_src.get_frame_time()

    def get_skeleton_dict(self):
        desc = self.skeleton.to_unity_format(animated_joints=self.animated_joints)
        #print(self.animated_joints, desc["jointDescs"])
        return desc

    def set_direction(self, direction_vector):
        if self.src_component_key == "morphablegraph_state_machine":
            length = np.linalg.norm(direction_vector)
            if length > 0:
                self.animation_src.direction_vector = direction_vector/length
                self.animation_src.target_projection_len = length
            else:
                self.animation_src.target_projection_len = 0

    def schedule_action(self, action, position=None):
        print("schedule action", action, position)
        if self.src_component_key == "morphablegraph_state_machine":
            if position is not None:
                self.animation_src.set_action_constraint(action["name"], action["keyframe"], position, action["joint"])
            self.animation_src.transition_to_action(action["name"])

    def schedule_action_path(self, action_desc, dt=STANDARD_DT, refresh=False):
        #print("schedule action with path", action_desc)
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.enqueue_states(action_desc, dt, refresh)

    def set_avatar_position(self, position):
        print("set position", position)
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.set_global_position(position)

    def set_avatar_orientation(self, orientation):
        print("set orientation", orientation)
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.set_global_orientation(orientation)

    def unpause_motion(self):
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.unpause()


