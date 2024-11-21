from threading import Thread, Event

from vision.detector import Detector
from vision.display import Display
from vision.camera import Camera
from vision.utils import InterestRegion

from robot.robot import RobotControl
from pipe.data_flow import DataFlow

"""
-93.6 = -25.39 + x : x =  68.21
-540 = -(-223) + y : y = -763
159 = -631 + z : z = 790
"""

class Main:
    def __init__(self) -> None:

        self.model = "D:/Thnnathat/Models/v1_Garbage NoDamage In Environment Only Normal_100epoch/weights/best.pt"
        # self.model = "D:/Thnnathat/Models/v2_arbage NoDamage In Environment Only/weights/best.pt"
        # self.model = "D:/Thnnathat/Models/v1_Garbage In Environment Onlyyyy_270epoch/weights/best.pt"
        # self.model = "yolov8m.pt"
        # self.model = "D:/Thnnathat/vrws_project/best.pt" # ? Color cube

        z_to_obj = 30
        z_gripper = 150

        x_p_rc = -60
        y_p_rc = -820
        # z_p_rc = (640 + z_gripper) - z_to_obj
        z_p_rc = (700 + z_gripper) - z_to_obj

        # self.cam_position: tuple[float, float, float] = [60 + x_offest, 830 + y_offest, 650 + z_offest + z_gripper - z_to_obj]
        self.cam_robot_position: tuple[float, float, float] = [x_p_rc, y_p_rc, z_p_rc]
        
        self.roi = InterestRegion()
        self.roi.offest_x = 500
        self.roi.offest_y = 100
        self.roi.width = 1000
        self.roi.height = 1000
        self.roi.set_poly_point((550, 0), (480, 800), (1400, 800), (1350, 0)) # (left, top), (left, bottom), (right, bottom), (right, top) ## Corners ##
        self.roi.roi_shape = "polygon"
        
        # self.drop_points = {
        #     "red-cube": [303, -151, 200],
        #     "green-cube": [303, -306, 300],
        #     "blue-cube": [303, -470, 300],
        #     "yellow-cube": [303, -628, 300],
        # }

        self.drop_points = {
            "bottle-plastic": [-511, -251, 340],
            "cans-aluminium": [-511, -627, 340],
            "clothes": [-511, -627, 340]
        }

    def start(self):
        det_cam_event = Event()
        cam_data_event = Event()
        
        #################################### ตัวตรวจจับ ####################################
        detector = Detector(det_cam_event, self.model, conf_thres=0.8)
        t_detector = Thread(name="Thread Detector", daemon=True, target=detector.torch_thread)
        t_detector.start()

        #################################### กล้อง ####################################
        camera = Camera(det_cam_event, cam_data_event, detector, self.roi)
        t_camera = Thread(name="Thread Camera", daemon=True, target=camera.camera_thread)
        t_camera.start()

        #################################### จัดการข้อมูลวัตถุเพื่อนำไปใช้ ####################################
        data_flow = DataFlow(cam_data_event, camera)
        t_data_flow = Thread(name="Thread Dataflow", daemon=True, target=data_flow.dataflow_thread)
        t_data_flow.start()
        
        #################################### ควบคุมแขนกล ####################################
        robot = None
        robot = RobotControl(self.drop_points, detector, data_flow, self.cam_robot_position, '192.168.1.6')
        t_robot = Thread(name="Thread Robot", daemon=True, target=robot.robot_thread)
        t_robot.start()
        
        #################################### ตัวตรวจจับ ####################################
        display = Display(detector, camera, self.roi)
        t_display = Thread(name="Thread Display", target=display.display_thread)
        t_display.start()

        t_display.join() ## รอให้ OpenCV ปิด

        ## หยุดการทำงานของ Thread อื่นๆ
        if detector is not None:
            detector.stop()
        if camera is not None: 
            camera.stop()
        if data_flow is not None:
            data_flow.stop()
        if robot is not None:
            robot.stop()


if __name__ == "__main__":
    main = Main()
    main.start()