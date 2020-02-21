
PCSKELETON = {
    "Spine": {
        "parent": "LowerBack",
      #  "x_axis_index": 3,
        "index": 7
    },
    "RightHand": {
        "parent": "RightForeArm",
       # "x_axis_index": 23,
        "index": 16
    },
    "RightUpLeg": {
        "parent": "RHipJoint",
       # "x_axis_index": 31,
        "index": 1
    },
    "RightLeg": {
        "parent": "RightUpLeg",
       # "x_axis_index": 33,
        "index": 2
    },
    "RightForeArm": {
        "parent": "RightArm",
       # "x_axis_index": 29,
        "index": 15
    },
    "LeftForeArm": {
        "parent": "LeftArm",
       # "x_axis_index": 13,
        "index": 19
    },
    "RightArm": {
        "parent": "RightShoulder",
       # "x_axis_index": 19,
        "index": 14
    },
    "Hips": {
        "parent": None,
       # "x_axis_index": 1,
        "index": 0
    },
    "LeftFoot": {
        "parent": "LeftLeg",
        #"x_axis_index": 35,
        "index": 6
    },
    "RightShoulder": {
        "parent": "Spine1",
        #"x_axis_index": 17,
        "index": 13
    },
    "LeftShoulder": {
        "parent": "Spine1",
        #"x_axis_index": 9,
        "index": 17
    },
    "Neck1": {
        "parent": "Neck",
       # "x_axis_index": 7,
        "index": 11
    },
    "LeftArm": {
        "parent": "LeftShoulder",
       # "x_axis_index": 11,
        "index": 18
    },
    "LeftLeg": {
        "parent": "LeftUpLeg",
       # "x_axis_index": 27,
        "index": 5
    },
    "LeftUpLeg": {
        "parent": "LHipJoint",
        #"x_axis_index": 25,
        "index": 4
    },
    "LeftHand": {
        "parent": "LeftForeArm",
       # "x_axis_index": 15,
        "index": 20
    },
    "RightFoot": {
        "parent": "RightLeg",
        #"x_axis_index": 37,
        "index": 3
    },
    "Spine1": {
        "parent": "Spine",
        #"x_axis_index": 5,
        "index": 8
    }
}
MODEL_OFFSET = [0,0,0]