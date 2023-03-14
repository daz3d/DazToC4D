import c4d

"""
Storing the AutoIK Hardcoded values to be replaced later down the road
so this isn't necessary
"""

"""Face Capture
"""
# facial_morphs = [
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_BLINK,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_LOOKDOWN,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_LOOKIN,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_LOOKOUT,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_LOOKUP,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_SQUINT,
#     c4d.FACECAPTURE_BLENDSHAPE_LEFTEYE_WIDE,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_BLINK,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_LOOKDOWN,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_LOOKIN,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_LOOKOUT,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_LOOKUP,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_SQUINT,
#     c4d.FACECAPTURE_BLENDSHAPE_RIGHTEYE_WIDE,
#     c4d.FACECAPTURE_BLENDSHAPE_JAW_FORWARD,
#     c4d.FACECAPTURE_BLENDSHAPE_JAW_LEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_JAW_RIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_JAW_OPEN,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_CLOSE,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_FUNNEL,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_PUCKER,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_LEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_RIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_SMILELEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_SMILERIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_FROWNLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_FROWNRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_DIMPLELEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_DIMPLERIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_STRETCHLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_STRETCHRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_ROLLLOWER,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_ROLLUPPER,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_SHRUGLOWER,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_SHRUGUPPER,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_PRESSLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_PRESSRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_LOWERDOWNLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_LOWERDOWNRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_UPPERUPLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_MOUTH_UPPERUPRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_BROW_DOWNLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_BROW_DOWNRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_BROW_INNERUP,
#     c4d.FACECAPTURE_BLENDSHAPE_BROW_OUTERUPLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_BROW_OUTERUPRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_CHEEK_PUFF,
#     c4d.FACECAPTURE_BLENDSHAPE_CHEEK_SQUINTLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_CHEEK_SQUINTRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_NOSE_SNEERLEFT,
#     c4d.FACECAPTURE_BLENDSHAPE_NOSE_SNEERRIGHT,
#     c4d.FACECAPTURE_BLENDSHAPE_TONGUE_OUT
# ]

""" [ ctrl_joint, joint ]
"""
constraint_joints = [
    ["Collar", "jCollar"],
    ["ShldrBend", "jArm"],
    ["ForearmBend", "jForeArm"],
    ["Shldr", "jArm"],  # Genesis 2
    ["ForeArm", "jForeArm"],  # Genesis 2
    ["Hand", "jHand"],
    ["hip", "jPelvis"],
    ["pelvis", "jPelvis"],
    ["abdomenLower", "jSpine"],
    ["abdomenUpper", "jAbdomenUpper"],
    ["chestLower", "jChest"],
    ["chestUpper", "jChestUpper"],
    ["neckLower", "jNeck"],
    ["abdomen", "jSpine"],  # Genesis 2
    ["chest", "jChest"],  # Genesis 2
    ["neck", "jNeck"],  # Genesis 2
    ["head", "jHead"],
    ["ThighBend", "jUpLeg"],
    ["Thigh", "jUpLeg"],  # Genesis 2
    ["Foot", "jFoot"],
    ["Shin", "jLeg"],
    ["Toe", "jToes"],
    ["Index1", "jIndex1"],
    ["Index2", "jIndex2"],
    ["Index3", "jIndex3"],
    ["Mid1", "jMiddle1"],
    ["Mid2", "jMiddle2"],
    ["Mid3", "jMiddle3"],
    ["Ring1", "jRing1"],
    ["Ring2", "jRing2"],
    ["Ring3", "jRing3"],
    ["Pinky1", "jPink1"],
    ["Pinky2", "jPink2"],
    ["Pinky3", "jPink3"],
    ["Thumb1", "jThumb1"],
    ["Thumb2", "jThumb2"],
    ["Thumb3", "jThumb3"],
]

constraint_joints_g9 = [
    ["_shoulder", "jCollar"],
    ["_upperarm", "jArm"],
    ["_forearm", "jForeArm"],
    #["_forearmtwist1", "ForearmTwist_ctrl"],
    ["_hand", "jHand"],
    ["hip", "jPelvis"], ## shared
    ["pelvis", "jPelvis"], ## shared
    ["spine1", "jSpine"],
    ["spine2", "jAbdomenUpper"],
    ["spine3", "jChest"],
    ["spine4", "jChestUpper"],
    ["neck1", "jNeck"],
    ["head", "jHead"], ## shared
    ["_thigh", "jUpLeg"],
    ["_foot", "jFoot"],
    ["_shin", "jLeg"],
    ["_toes", "jToes"],
    ["_index1", "jIndex1"],
    ["_index2", "jIndex2"],
    ["_index3", "jIndex3"],
    ["_mid1", "jMiddle1"],
    ["_mid2", "jMiddle2"],
    ["_mid3", "jMiddle3"],
    ["_ring1", "jRing1"],
    ["_ring2", "jRing2"],
    ["_ring3", "jRing3"],
    ["_pinky1", "jPink1"],
    ["_pinky2", "jPink2"],
    ["_pinky3", "jPink3"],
    ["_thumb1", "jThumb1"],
    ["_thumb2", "jThumb2"],
    ["_thumb3", "jThumb3"],
]

rig_joints = [
    ["Collar", "jCollar"],
    ["ShldrBend", "jArm"],
    ["ForearmBend", "jForeArm"],
    ["Shldr", "jArm"],  # Genesis 2
    ["ForeArm", "jForeArm"],  # Genesis 2
    ["Hand", "jHand"],
    ["hip", "jPelvis"],
    ["pelvis", "jPelvis"],
    ["abdomenLower", "jSpine"],
    ["abdomenUpper", "jAbdomenUpper"],
    ["chestLower", "jChest"],
    ["chestUpper", "jChestUpper"],
    ["neckLower", "jNeck"],
    ["abdomen", "jSpine"],  # Genesis 2
    ["chest", "jChest"],  # Genesis 2
    ["neck", "jNeck"],  # Genesis 2
    ["head", "jHead"],
    ["ThighBend", "jUpLeg"],
    ["Thigh", "jUpLeg"],  # Genesis 2
    ["Foot", "jFoot"],
    ["Shin", "jLeg"],
    ["Toe", "jToes"],
    ["SmallToe2_2", "jToes_end"],
    ["Index1", "jIndex1"],
    ["Index2", "jIndex2"],
    ["Index3", "jIndex3"],
    ["Mid1", "jMiddle1"],
    ["Mid2", "jMiddle2"],
    ["Mid3", "jMiddle3"],
    ["Ring1", "jRing1"],
    ["Ring2", "jRing2"],
    ["Ring3", "jRing3"],
    ["Pinky1", "jPink1"],
    ["Pinky2", "jPink2"],
    ["Pinky3", "jPink3"],
    ["Thumb1", "jThumb1"],
    ["Thumb2", "jThumb2"],
    ["Thumb3", "jThumb3"],
]

rig_joints_g9 = [
    ["_shoulder", "jCollar"],
    ["_upperarm", "jArm"],
    ["_forearm", "jForeArm"],
    #["_forearmtwist1", "ForearmTwist_ctrl"],
    ["_hand", "jHand"],
    ["hip", "jPelvis"], ## shared
    ["pelvis", "jPelvis"], ## shared
    ["spine1", "jSpine"],
    ["spine2", "jAbdomenUpper"],
    ["spine3", "jChest"],
    ["spine4", "jChestUpper"],
    ["neck1", "jNeck"],
    ["head", "jHead"], ## shared
    ["_thigh", "jUpLeg"],
    ["_foot", "jFoot"],
    ["_shin", "jLeg"],
    ["_toes", "jToes"],
    ["_index1", "jIndex1"],
    ["_index2", "jIndex2"],
    ["_index3", "jIndex3"],
    ["_mid1", "jMiddle1"],
    ["_mid2", "jMiddle2"],
    ["_mid3", "jMiddle3"],
    ["_ring1", "jRing1"],
    ["_ring2", "jRing2"],
    ["_ring3", "jRing3"],
    ["_pinky1", "jPink1"],
    ["_pinky2", "jPink2"],
    ["_pinky3", "jPink3"],
    ["_thumb1", "jThumb1"],
    ["_thumb2", "jThumb2"],
    ["_thumb3", "jThumb3"],
    ["_midtoe2", "jToes_end"],
]

""" [ Guide, joint ]
"""
guides_for_rig = [
    ["Collar", "l_shoulder", "lCollar", "chest"],
    ["AbdomenUpper", "spine2", "abdomenUpper"],
    ["ChestUpper", "spine4", "chestUpper"],
    ["Shoulder", "l_upperarm", "lShldrBend", "lShldr"],
    ["Elbow", "l_forearm", "lForearmBend", "lForeArm"],
    #["ForearmTwist", "l_forearmtwist1"],
    ["Hand", "l_hand", "lHand"],
    ["Index1", "l_index1", "lIndex1"],
    ["Index2", "l_index2", "lIndex2"],
    ["Index3", "l_index3", "lIndex3"],
    ["Index_end", "l_index3", "lIndex3"],
    ["Middle1", "l_mid1", "lMid1"],
    ["Middle2", "l_mid2", "lMid2"],
    ["Middle3", "l_mid3", "lMid3"],
    ["Middle_end", "l_mid3", "lMid3"],
    ["Ring1", "l_ring1", "lRing1"],
    ["Ring2", "l_ring2", "lRing2"],
    ["Ring3", "l_ring3", "lRing3"],
    ["Ring_end", "l_ring3", "lRing3"],
    ["Pinky1", "l_pinky1", "lPinky1"],
    ["Pinky2", "l_pinky2", "lPinky2"],
    ["Pinky3", "l_pinky3", "lPinky3"],
    ["Pinky_end", "l_pinky3", "lPinky3"],
    ["Thumb1", "l_thumb1", "lThumb1"],
    ["Thumb2", "l_thumb2", "lThumb2"],
    ["Thumb3", "l_thumb3", "lThumb3"],
    ["Thumb_end", "l_thumb3", "lThumb3"],
    ["LegUpper", "l_thigh", "lThighBend", "lThigh"],
    ["Knee", "l_shin", "lShin"],
    ["Foot", "l_foot", "lFoot"],
    ["Toes", "l_toes", "lToe"],
    ["Toes_end", "l_midtoe2", "lSmallToe2_2"],
    ["Toes_end", "l_midtoe1", "lSmallToe2"],
    ["Pelvis", "hip"],
    ["Spine_Start", "spine1", "abdomenLower", "abdomen"],
    ["Chest_Start", "spine3", "chestLower", "chest"],
    ["Neck_Start", "neck1", "neckLower", "neck"],
    ["Neck_End", "head"],
    ["Head_End", "head_end"],  # Labeled temp...
]

guides_to_mirror = [
    "Pinky_end",
    "Pinky3",
    "Pinky2",
    "Pinky1",
    "Ring_end",
    "Ring3",
    "Ring2",
    "Ring1",
    "Middle_end",
    "Middle3",
    "Middle2",
    "Middle1",
    "Index_end",
    "Index3",
    "Index2",
    "Index1",
    "Thumb_end",
    "Thumb2",
    "Thumb3",
    "Thumb1",
    "Hand",
    #"ForearmTwist",
    "Elbow",
    "Shoulder",
    "Toes_end",
    "Toes",
    "Foot",
    "Knee",
    "LegUpper",
]

""" [ ctrl_joint, Parent, Guide ]
"""
center_joints = [
    ["jPelvis", "", "Pelvis"],
    ["jSpine", "jPelvis", "Spine_Start"],
    ["jAbdomenUpper", "jSpine", "AbdomenUpper"],
    ["jChest", "jAbdomenUpper", "Chest_Start"],
    ["jChestUpper", "jChest", "ChestUpper"],
    ["jNeck", "jChestUpper", "Neck_Start"],
    ["jHead", "jNeck", "Neck_End"],
    ["jHeadEnd", "jHead", "Head_End"],
]

arm_joints = [
    ["jCollar", "jChestUpper", "Collar"],
    ["jArm", "jCollar", "Shoulder"],
    ["jForeArm", "jArm", "Elbow"],
    ["jHand", "jForeArm", "Hand"],
]

leg_joints = [
    ["jUpLeg", "jPelvis", "LegUpper"],
    ["jLeg", "jUpLeg", "Knee"],
    ["jFoot", "jLeg", "Foot"],
    ["jFoot2", "", "Foot"],
    ["jToes", "jFoot2", "Toes"],
    ["jToes_end", "jToes", "Toes_end"],
]

thumb_joints = [
    ["jThumb1", "", "Thumb1"],
    ["jThumb2", "jThumb1", "Thumb2"],
    ["jThumb3", "jThumb2", "Thumb3"],
    ["jThumb_end", "jThumb3", "Thumb_end"],
]


""" [ ctrl_shape, joint, preset, constraint, parent ]
"""
ik_controls = [
    ["IK_Foot", "jFoot", "zeroRotInvisible"],
    ["Toe_Rot", "jToes", "sphereToe"],
    ["Foot_Roll", "jToes", "cube"],
    ["IK_Hand", "jHand", "cube"],
    ["Collar_ctrl", "jCollar", "collar"],
    ["Foot_Platform", "IK_Foot", "Foot_Platform"],
    ["ToesEnd", "jToes_end", "none"],
    ["Pelvis_ctrl", "jPelvis", "pelvis"],
    ["ForearmTwist_ctrl", "lForearmTwist", "twist"],
    ["ForearmTwist_ctrl___R", "rForearmTwist", "twist"],
    ["Spine_ctrl", "jSpine", "spine"],
    ["AbdomenUpper_ctrl", "jAbdomenUpper", "spine"],
    ["ChestUpper_ctrl", "jChestUpper", "spine"],
    ["Foot_PlatformBase", "jFoot", "Foot_PlatformNEW"],
    ["Foot_PlatformBase___R", "jFoot___R", "Foot_PlatformNEW"],
    ["Chest_ctrl", "jChest", "spine"],
    ["Neck_ctrl", "jNeck", "neck"],
    ["Head_ctrl", "jHead", "head"],
    ["ForearmTwist_ctrl", "l_forearmtwist1", "twist"],
    ["ForearmTwist_ctrl___R", "r_forearmtwist1", "twist"],
    ["ForearmTwist2_ctrl", "l_forearmtwist2", "twist"],
    ["ForearmTwist2_ctrl___R", "r_forearmtwist2", "twist"],
]

ik_tags = [
    ["jUpLeg", "jFoot", "IK_Foot", "jUpLeg.Pole", "LegUpper", "Negative"],
    ["jArm", "jHand", "IK_Hand", "jArm.Pole", "Shoulder", ""],
]

daz_controls = [
    ["IK_Foot", "Foot", "zeroRotInvisible", "None"],
    ["Toe_Rot", "Toe", "sphereToe", "None"],
    ["Foot_Roll", "Toe", "cube", "None"],
    ["IK_Hand", "Hand", "cube", "None"],
    ["Collar_ctrl", "Collar", "collar", ""],
    ["Foot_Platform", "IK_Foot", "Foot_Platform", "UPVECTOR"],
    ["Pelvis_ctrl", "hip", "pelvis"],
    ["ForearmTwist_ctrl", "lForearmTwist", "twist"],
    ["ForearmTwist_ctrl___R", "rForearmTwist", "twist"],
    ["Spine_ctrl", "abdomenLower", "spine"],
    ["AbdomenUpper_ctrl", "abdomenUppe", "spine"],
    ["ChestUpper_ctrl", "chestUpper", "spine"],
    ["Foot_PlatformBase", "Foot", "Foot_PlatformNEW"],
    ["Chest_ctrl", "chest", "spine"],
    ["Neck_ctrl", "neck", "neck"],
    ["Head_ctrl", "head", "head"],
]

daz_tags = [
    ["Shin", "Foot", "IK_Foot", "Shin.Pole", "ThighBend", "Negative"],
    ["ShldrBend", "Hand", "IK_Hand", "ShldrBend.Pole", "ForeArm", ""],
]
