class Animations:
    def check_animation_exists(self, joints):
        for joint in joints:
            tracks = joint.GetCTracks()
            if len(tracks) > 0:
                return True
