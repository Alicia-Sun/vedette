import os
import math
import paraview.simple as smp

#===============================================================================
#   Parameters
#===============================================================================

params = {}

params['trajectory_name'] = "Trajectory"
params['trajectory_orientation_array'] = "Orientation(AxisAngle)"
params['trajectory_time_array'] = "Time"
params['trajectory_to_animation_time_offset'] = 0
params['cad_model_name'] = ""
params['frames_output_dir'] = ""
params['image_resolution'] = (1920, 1080)
params['save_all_views_in_layout'] = False
params['filename_format'] = "%06d.png"
params['video_output_path'] = ""
params['video_framerate'] = 10.
params['verbose'] = True

#===============================================================================
#   Generic helpers
#===============================================================================

def get_pose_idx_from_time(trajectory_timesteps):
    animation_time = smp.GetAnimationScene().AnimationTime
    trajectory_timesteps_offset = [t + params['trajectory_to_animation_time_offset'] for t in trajectory_timesteps]
    return min(range(len(trajectory_timesteps_offset)), key=lambda i: abs(trajectory_timesteps_offset[i] - animation_time))


def update_camera(camera, pose_idx, position, orientation):
    if camera and camera.timestep_inside_range(pose_idx):
        view = smp.GetActiveView()
        view.CameraPosition = camera.interpolate_position(pose_idx, orientation, position, list(view.CameraPosition))
        view.CameraFocalPoint = camera.interpolate_focal_point(pose_idx, orientation, position)
        view.CameraViewUp = camera.interpolate_up_vector(pose_idx, orientation)
        view.CenterOfRotation = view.CameraFocalPoint
        return True
    return False


def update_cad_model(model, position, orientation):
    if model:
        model.Transform.Translate = position
        return True
    return False


def save_screenshot():
    if params['frames_output_dir']:
        if not hasattr(save_screenshot, 'image_index'):
            save_screenshot.image_index = 0
            if not os.path.isdir(params['frames_output_dir']):
                os.makedirs(params['frames_output_dir'])

        image_name = os.path.join(params['frames_output_dir'], params['filename_format'] % save_screenshot.image_index)
        view_or_layout = smp.GetLayout() if params['save_all_views_in_layout'] else smp.GetActiveView()
        smp.SaveScreenshot(image_name, view_or_layout, ImageResolution=params['image_resolution'])
        save_screenshot.image_index += 1
        return True
    return False


def generate_video():
    if params['video_output_path']:
        video_dir = os.path.dirname(params['video_output_path'])
        if not os.path.isdir(video_dir):
            os.makedirs(video_dir)

        images = os.path.join(params['frames_output_dir'], params['filename_format'])
        os.system("ffmpeg -framerate {} -i {} {}".format(params['video_framerate'], images, params['video_output_path']))
        return os.path.isfile(params['video_output_path'])
    return False

#===============================================================================
#   Animation cue methods
#===============================================================================

def start_cue_generic_setup(self):
    traj_src = smp.FindSource(params['trajectory_name'])
    self.trajectory = traj_src.GetClientSideObject().GetOutput() if traj_src else None
    self.model = smp.FindSource(params['cad_model_name']) if params['cad_model_name'] else None
    self.pose_idx = 0
    self.cameras = []


def tick(self):
    if not self.trajectory:
        print("Trajectory source is invalid")
        return

    if params['trajectory_time_array']:
        time_data = self.trajectory.GetPointData().GetArray(params['trajectory_time_array'])
        timesteps = [time_data.GetValue(i) for i in range(time_data.GetNumberOfTuples())]
        self.pose_idx = get_pose_idx_from_time(timesteps)
    else:
        self.pose_idx = self.trajectory.GetNumberOfPoints() - 1

    position = list(self.trajectory.GetPoints().GetData().GetTuple3(self.pose_idx))
    axis_angle = list(self.trajectory.GetPointData().GetArray(params['trajectory_orientation_array']).GetTuple4(self.pose_idx))
    orientation = [axis_angle[i] * axis_angle[3] for i in range(3)]

    for i, c in enumerate(self.cameras):
        if update_camera(c, self.pose_idx, position, orientation) and params['verbose']:
            print("time {}, pose {} : updating camera path {} of type '{}'".format(smp.GetAnimationScene().AnimationTime, self.pose_idx, i, c.type))

    update_cad_model(self.model, position, orientation)
    smp.Render()
    save_screenshot()


def end_cue(self):
    success = generate_video()
    if success and params['verbose']:
        print("Video saved to " + params['video_output_path'])
    if params['verbose']:
        print("End of the animation")
