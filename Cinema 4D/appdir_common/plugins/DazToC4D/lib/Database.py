"""
Storing the AutoIK Hardcoded values to be replaced later down the road 
so this isn't necessary
"""

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

""" [ Guide, joint ]
"""
guides_for_rig = [
    ["Collar", "lCollar", "chest"],
    ["AbdomenUpper", "abdomenUpper"],
    ["ChestUpper", "chestUpper"],
    ["Shoulder", "lShldr"],  # Genesis 2
    ["Elbow", "lForeArm"],  # Genesis 2
    ["Shoulder", "lShldrBend"],
    ["Elbow", "lForearmBend"],
    ["Hand", "lHand"],
    ["Index1", "lIndex1"],
    ["Index2", "lIndex2"],
    ["Index3", "lIndex3"],
    ["Index_end", "lIndex3"],
    ["Middle1", "lMid1"],
    ["Middle2", "lMid2"],
    ["Middle3", "lMid3"],
    ["Middle_end", "lMid3"],
    ["Ring1", "lRing1"],
    ["Ring2", "lRing2"],
    ["Ring3", "lRing3"],
    ["Ring_end", "lRing3"],
    ["Pinky1", "lPinky1"],
    ["Pinky2", "lPinky2"],
    ["Pinky3", "lPinky3"],
    ["Pinky_end", "lPinky3"],
    ["Thumb1", "lThumb1"],
    ["Thumb2", "lThumb2"],
    ["Thumb3", "lThumb3"],
    ["Thumb_end", "lThumb3"],
    ["LegUpper", "lThighBend"],
    ["LegUpper", "lThigh"],
    ["Knee", "lShin"],
    ["Foot", "lFoot"],
    ["Toes", "lToe"],
    ["Toes_end", "lSmallToe2_2"],
    ["Toes_end", "lSmallToe2"],
    ["Pelvis", "hip"],
    ["Spine_Start", "abdomenLower"],
    ["Chest_Start", "chestLower"],
    ["Neck_Start", "neckLower"],
    ["Neck_End", "head"],
    ["Spine_Start", "abdomen"],
    ["Chest_Start", "chest"],
    ["Neck_Start", "neck"],
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

side_joints = [
    ["jCollar", "jChestUpper", "Collar"],
    ["jArm", "jCollar", "Shoulder"],
    ["jForeArm", "jArm", "Elbow"],
    ["jHand", "jForeArm", "Hand"],
    ["jUpLeg", "jPelvis", "LegUpper"],
    ["jLeg", "jUpLeg", "Knee"],
    ["jFoot", "jLeg", "Foot"],
    ["jFoot2", "", "Foot"],
    ["jToes", "jFoot2", "Toes"],
    ["jToes_end", "jToes", "Toes_end"],
]

finger_joints = [
    ["jThumb1", "", "Thumb1"],
    ["jThumb2", "jThumb1", "Thumb2"],
    ["jThumb3", "jThumb2", "Thumb3"],
    ["jThumb_end", "jThumb3", "Thumb_end"],
]
