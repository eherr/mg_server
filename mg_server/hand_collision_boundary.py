import collections
import numpy as np
from vis_utils.scene.components import ComponentBase
from vis_utils.graphics.geometry.mesh import Mesh
from vis_utils.graphics import  materials

PRIMITIVE_BODY_DENSITY = 1

def smooth(points):
    return points

class HandCollisionBoundaryComponent(ComponentBase):
    def __init__(self, joint_name, radius, animation_src, scene_object, visualize=True, density=PRIMITIVE_BODY_DENSITY):
        ComponentBase.__init__(self, scene_object)
        visualize = True
        if visualize:
            material = materials.red
            self.mesh = Mesh.build_sphere(20, 20, radius * 2, material)
        else:
            self.mesh = None
        self.joint_name = joint_name
        kinematic = True
        self.src_controller = self.scene_object._components[animation_src]
        self.skeleton = self.src_controller.skeleton
        print("create collision boundy")
        name = str(scene_object.node_id) + "_body"
        orientation = [1,0,0,0]
        position = scene_object.getPosition()
        self.transformation = np.eye(4)
        self.scene = self.scene_object.scene
        self.sim = self.scene_object.scene.sim
        self.body = self.sim.create_sphere_body(name, position, orientation, radius, kinematic, density)
        self.body_id = self.body.get_id()
        self.active = True
   
    def update(self, dt):
        if not self.active:
            return
        frame = self.src_controller.get_current_frame()
        position = self.skeleton.nodes[self.joint_name].get_global_position(frame)
        self.transformation[3,:3] = position
        self.body.set_position(position)

    def check_trajectory(self, trajectory, dt):
        self.sim.save_state()
        has_contact = False
        pos = None
        normal = None
        frame_idx = -1
        idx = 0
        for point in trajectory:
            self.scene.mutex.acquire()
            self.body.set_position(point)
            self.sim.update(dt)
            has_contact, pos, normal = self.has_contact()
            self.scene.mutex.release()
            if has_contact:
                frame_idx = idx
                break
            idx+=1
        self.sim.restore_state()
        print("check collision", has_contact, frame_idx, len(trajectory))
        return frame_idx, pos, normal

    def get_delta_trajectory(self, trajectory, dt):
        """ find contact point and prevent further movement in direction to contact point until end of collision"""
        print("check for collision")
        self.sim.save_state()
        idx = 0
        has_contact = False
        delta_trajectory = collections.OrderedDict()
        dir_to_contact = None
        cashed_joint_pos = None
        for joint_pos in trajectory:
            self.scene.mutex.acquire()
            self.body.set_position(joint_pos)
            self.sim.update(dt)
            contact, pos, normal = self.has_contact()
            #normal = np.array([0,0,1]) #TODO get better normal
            self.scene.mutex.release()
            if contact:
                if cashed_joint_pos is None:
                    dir_to_contact = pos - joint_pos
                    dir_to_contact /= np.linalg.norm(dir_to_contact)
                    cashed_joint_pos = joint_pos
                else:
                    #project difference along direction to contact
                    delta = joint_pos- cashed_joint_pos
                    dot = np.dot(delta, dir_to_contact)
                    dot = abs(dot)
                    #store negative projected difference as normal to prevent further movement into that direction
                    delta_trajectory[idx] = - (dot * dir_to_contact)
                    has_contact = True
                #print("collision", idx, new_pos, point, delta_trajectory[idx])
            else:
                dir_to_contact = None
                cashed_joint_pos = None
            idx+=1
        self.sim.restore_state()
        #delta_trajectory = np.array(delta_trajectory)
        #fixed_trajectory = trajectory+smooth(delta_trajectory)

        print("check for collision", has_contact)
        return has_contact,delta_trajectory#fixed_trajectory

    def has_contact(self):
        has_contact = False
        pos = None
        normal = None
        self.sim.update_contacts()
        for contact in self.sim.contacts:
            if not contact.ground and (contact.body1 == self.body_id or contact.body2 == self.body_id):
                has_contact = True
                pos = np.array(contact.pos)
                normal = np.array(contact.normal)
                break
        return has_contact, pos, normal

    def get_geometry_list(self):
        if self.mesh is not None:
            return [self.mesh]
        else:
            return None
