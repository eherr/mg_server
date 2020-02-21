from vis_utils.scene.components.component_base import ComponentBase
from vis_utils.scene.components.terrain_component import TerrainComponent
import tornado.ioloop
import tornado.web
import json
import threading
import asyncio
import os
from PIL import Image
from .morphable_graph_state_machine import MotionStateGraphLoader




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
        self.web_app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def stop(self):
        print("stopping server")
        tornado.ioloop.IOLoop.instance().stop()


class BaseHandler(tornado.web.RequestHandler):
    """ https://stackoverflow.com/questions/35254742/tornado-server-enable-cors-requests"""

    def set_default_headers(self):
        self.set_header("access-control-allow-origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS')
        # HEADERS!
        self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin,authorization,content-type")

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

    def get(self):
        error_string = "GET request not implemented. Use POST instead."
        print(error_string)
        self.write(error_string)

class SetHeightMapHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.app = application

    @tornado.gen.coroutine
    def post(self):
        try:
            input_str = self.request.body.decode("utf-8")
            data = json.loads(input_str)
            answer_str = self.app.server.set_height_map(data)
            self.write(answer_str)

        except Exception as e:
            print("caught exception in post")
            self.write("Caught an exception: %s" % e)
            raise
        finally:
            self.finish()


class ReloadMotionStateGrapHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.app = application


    @tornado.gen.coroutine
    def post(self):
        try:
            input_str = self.request.body.decode("utf-8")
            data = json.loads(input_str)
            if "graph_id" in data and "port" in data:
                answer_str = self.app.server.reload_motion_state_graph(data["port"], data["graph_id"])
            self.write(answer_str)

        except Exception as e:
            print("caught exception in post")
            self.write("Caught an exception: %s" % e)
            raise
        finally:
            self.finish()

class WebApp(tornado.web.Application):
    """ extends the Application class by a list of connections to allow access from other classes
    """
    def __init__(self, server, handlers=None, default_host="", transforms=None, **settings):
        self.server = server
        tornado.web.Application.__init__(self, handlers, default_host, transforms)


class SceneInterface(ComponentBase):
    def __init__(self, scene_object, port):
        ComponentBase.__init__(self, scene_object)
        self._scene_object = scene_object
        self.scene = scene_object.scene
        self.port = port
        self.web_app = WebApp(self, [(r"/set_height_map", SetHeightMapHandler),(r"/reload_state_graph", ReloadMotionStateGrapHandler)
                                       ])
        self.server_thread = ServerThread(self.web_app, port)
        self.db_url = "localhost:8889/"


    def start(self):
        self.server_thread.start()
        print("started scene REST interface on port ", self.port)

    def stop(self):
        self.server_thread.stop()
        print("stopped scene REST interface on port ", self.port)

    def set_height_map(self, data):
        mesh = None
        success = False
        if "image_path" in data:
            image_path = data["image_path"]
            width = data["width"]
            depth = data["depth"]
            scale = [1.0, 1.0]
            if "scale" in data:
                scale = data["scale"]
            height_scale = data["height_scale"]
            if os.path.isfile(image_path):
                with open(image_path, "rb") as input_file:
                    img = Image.open(input_file)
                    height_map_image = img.copy()  # work with a copy of the image to close the file
                    img.close()
                    pixel_is_tuple = not image_path.endswith("bmp")
                    success = True

        elif "image" in data:
            import base64
            size = data["size"]
            mode = data["mode"]
            width = data["width"]
            depth = data["depth"]
            height_scale = data["height_scale"]
            height_map_image = Image.frombytes(mode, size, base64.decodebytes(data["image"]))
            success = success


        if success:
            builder = self.scene.object_builder
            build_terrain = builder.construction_methods["terrain"]
            self.scene.schedule_func_call("terrain", build_terrain, (builder, width, depth, height_map_image, height_scale))
            return "OK"
        else:
            return "Missing required data"

    def reload_motion_state_graph(self, port, graph_id):
        loader = MotionStateGraphLoader()
        loader.use_all_joints = True
        skeleton_name = "custom"
        frame_time = 1.0/72
        start_node = ("walk", "idle_custom_1")
        graph = loader.build_from_database(self.db_url, skeleton_name, graph_id, frame_time)
        o = self.scene.find_object_by_name("morphablegraph_state_machine"+str(port))
        if o is not None:
            if "animation_server" in o._components and "morphablegraph_state_machine" in o._components:
                animation_server = o._components["animation_server"]
                #animation_server.stop()
                graph_controller = o._components["morphablegraph_state_machine"]
                self.scene.schedule_func_call("reload_graph", graph_controller.set_graph, (graph, start_node ))
                return "OK"
            else:
                print("Error Could not find components")
                return "Error Could not find components"
        else:
            print("Error Could not find scene objects")
            return "Could not find scene object"


