
import numpy as np
from vis_utils.scene.components import ComponentBase
from vis_utils.graphics.geometry.mesh import Mesh
from vis_utils.graphics import  materials

ODE_DIRECTION_MAP ={"x": 1, "y": 2, "z": 3, "-x": -1, "-y": -2, "-z": -3}

PRIMITIVE_BODY_DENSITY = 1

#MAX_VEL = 100000
MAX_VEL = 1000#00
MAX_VEL = 500
MAX_VEL = 250
MAX_VEL = 100

class CollisionBoundaryComponent(ComponentBase):
    def __init__(self, radius,length, animation_src, scene_object, visualize=True, density=PRIMITIVE_BODY_DENSITY):
        ComponentBase.__init__(self, scene_object)
        direction="y"
        if visualize:
            material = materials.red
            self.mesh = Mesh.build_capsule(20, 20, radius * 2, length, direction, material)
        else:
            self.mesh = None
        kinematic = True
        self.src_controller = self.scene_object._components[animation_src]
        name = str(scene_object.node_id) + "_body"
        capsule_dir = ODE_DIRECTION_MAP[direction]
        orientation = [1,0,0,0]
        position = scene_object.getPosition()
        self.transformation = np.eye(4)
        self.y_offset = length/2
        self.sim = self.scene_object.scene.sim
        self.body = self.sim.create_cylinder_body(name, position, orientation, length, radius, capsule_dir, True, kinematic, density)
        self.body_id = self.body.get_id()
        self.active = True
   
    def update(self, dt):
        if not self.active:
            return
        has_contact = False
        position = np.array(self.src_controller.getPosition())
        for contact in self.sim.contacts:
            if not contact.ground and (contact.body1 == self.body_id  or contact.body2 == self.body_id):
                vector = position - contact.pos
                vector[1] = 0
                vector /= np.linalg.norm(vector)
                #normal = np.array(contact.normal)
                #force_vector = np.array(contact.force)
                velocity = MAX_VEL#min(np.linalg.norm(force_vector), MAX_VEL)
                delta = vector * velocity*dt#
                position += delta
                has_contact = True
        if has_contact:
            self.src_controller.set_global_position(position)
        position[1] += self.y_offset
        self.transformation[3,:3] = position
        self.body.set_position(position)

    def check_trajectory(self, trajectory, dt):
        self.sim.save_state()
        has_contact = False
        for point in trajectory:
            #point[1] += self.y_offset
            self.body.set_position(point)
            self.sim.update(dt)
            if self.has_contact():
                has_contact = True
                break
        self.sim.restore_state()
        return has_contact

    def has_contact(self):
        has_contact = False
        for contact in self.sim.contacts:
            if not contact.ground and (contact.body1 == self.body_id or contact.body2 == self.body_id):
                has_contact = True
                break
        return has_contact

    def get_geometry_list(self):
        if self.mesh is not None:
            return [self.mesh]
        else:
            return None
