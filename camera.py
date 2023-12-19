import cv2
import numpy as np
from picamera2 import Picamera2
import threading
import math

def img_read(path, size=(640,360)):
    img = cv2.imread(path)
    img = cv2.resize(img, size)
    
    return img

def filter_img(img):
    # hsv 색 공간으로 변환
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 상한, 하한 색 범위 지정
    bound_lower = np.array([20, 35, 20])
    bound_upper = np.array([50, 220, 255])
    mask = cv2.inRange(hsv_img, bound_lower, bound_upper)
    
    # 모폴로지 연산
    kernel = np.ones((7,7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    filtered_img = cv2.bitwise_and(img, img, mask=mask)

    return filtered_img

def edge_detection(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 100, 150)
    # sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
    # canny = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
    # canny = cv2.addWeighted(cv2.convertScaleAbs(sobel_x), 0.5, cv2.convertScaleAbs(sobel_y), 0.5, 0)

    return canny

def region_of_interest(img):
    trap_bottom_width = 0.95
    trap_top_width = 0.8
    trap_height = 0.3

    height, width = img.shape[:2]
    
    mask = np.zeros((height, width, 1), np.uint8)

    left_bottom = [width*(1-trap_bottom_width), height]
    right_bottom = [width*trap_bottom_width, height]
    left_top = [width*(1-trap_top_width), height*trap_height]
    right_top = [width*trap_top_width, height*trap_height]

    trap = np.array([left_bottom, left_top, right_top, right_bottom], np.int32)

    mask = cv2.fillConvexPoly(mask, trap, 255)

    roi = cv2.bitwise_and(img, img, mask=mask)

    return roi

def hough_line(img):
    threshold = 20
    minLineLength = 10
    maxLineGap = 20
    lines = cv2.HoughLinesP(img, 1, np.pi/180, threshold, None, minLineLength, maxLineGap)

    return lines
    
def extract_line(img):
    
    lines = hough_line(img)
    
    left_line = []
    right_line = []
    img_center = img.shape[1] / 2

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]

            slope = (y2-y1) / (x2-x1) + 0.00001

            if slope < 0 and (x1 < img_center and x2 < img_center):
                left_line.append(line)
            elif slope > 0 and (x1 > img_center and x2 > img_center):
                right_line.append(line)

    # height, width = img.shape[:2]
    # line_img = np.zeros((height, width, 3), np.uint8)

    # for line in left_line:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(line_img, (x1,y1), (x2,y2), (0,255,0), 1)
    
    # for line in right_line:
    #     x1, y1, x2, y2 = line[0]
    #     cv2.line(line_img, (x1,y1), (x2,y2), (0,255,0), 1)
    
    # cv2.imshow('line',line_img)
    
    return (left_line, right_line)


def regression(line, size):
    trap_bottom_width = 0.95
    trap_top_width = 0.8
    trap_height = 0.3

    w, h = size
    
    left_line, right_line = line

    left_points = []
    if len(left_line) > 0:
        for line in left_line:
            start = [line[0][0], line[0][1]]
            end = [line[0][2], line[0][3]]
            left_points.append(start)
            left_points.append(end)
    else:
        start = [w*(1-trap_bottom_width), h]
        end = [w*(1-trap_top_width), h*trap_height]
        left_points.append(start)
        left_points.append(end)

    left_points = np.asarray(left_points)
        
    left = cv2.fitLine(left_points, cv2.DIST_L2, 0, 0.01, 0.01)
    left_gradient = (left[1] / left[0])
    left_bias = (left[2][0], left[3][0])

    right_points = []
    if len(right_line) > 0:
        for line in right_line:
            start = [line[0][0], line[0][1]]
            end = [line[0][2], line[0][3]]
            right_points.append(start)
            right_points.append(end)
    else:
        start = [w*trap_bottom_width, h]
        end = [w*trap_top_width, h*trap_height]
        right_points.append(start)
        right_points.append(end)

    right_points = np.asarray(right_points)
    
    right = cv2.fitLine(right_points, cv2.DIST_L2, 0, 0.01, 0.01)
    right_gradient = (right[1] / right[0])
    right_bias = (right[2][0], right[3][0])
    
    start_y = h
    end_y = h*trap_height

    right_start_x = (start_y - right_bias[1]) / right_gradient[0] + right_bias[0]
    right_end_x = (end_y - right_bias[1]) / right_gradient[0] + right_bias[0]

    left_start_x = (start_y - left_bias[1]) / left_gradient[0] + left_bias[0]
    left_end_x = (end_y - left_bias[1]) / left_gradient[0] + left_bias[0]

    return [(left_start_x, start_y), (left_end_x, end_y), (right_start_x, start_y), (right_end_x, end_y)]

def predict_direct(img, roi):
  
    h,w = img.shape[:2]
    img_center = w / 2

    lines = extract_line(roi)
    line_points = regression(lines, (w,h))

    left_start, left_end, right_start, right_end = line_points

    x1, y1 = left_start
    x2, y2 = left_end
    x3, y3 = right_start
    x4, y4 = right_end

    left_gradient = (y2-y1) / (x2-x1)
    right_gradient = (y4-y3) / (x4-x3)
    left_bias = y2-left_gradient*x2
    right_bias = y4-right_gradient*x4

    left_start_y = h
    left_start_x = (h-left_bias) / left_gradient
    if left_start_x < 0 or math.isnan(left_start_x):
        left_start_x = 0
        left_start_y = left_bias
    
    left_end_y = 0
    left_end_x = (-1*left_bias) / left_gradient
    if left_end_x > w or math.isnan(left_end_x):
        left_end_x = w
        left_end_y = w*left_gradient + left_bias
    
    # y = mx + b
    right_start_y = h
    right_start_x = (h-right_bias) / right_gradient
    if right_start_x > w or math.isnan(right_start_x):
        right_start_x = w
        right_start_y = right_gradient*w + right_bias

    right_end_y = 0
    right_end_x = (-1*right_bias) / right_gradient
    if right_end_x < 0 or math.isnan(right_end_x):
        right_end_x = 0
        right_end_y = right_bias
    

    if not math.isnan(left_start_y) and not math.isnan(left_end_y) and not math.isnan(right_start_y) and not math.isnan(right_end_y):
        left_start=(int(left_start_x), int(left_start_y))
        left_end = (int(left_end_x), int(left_end_y))
        right_start = (int(right_start_x), int(right_start_y))
        right_end = (int(right_end_x), int(right_end_y))

        cv2.line(img, left_start, left_end, (0,255,0), 2)
        cv2.line(img, right_start, right_end, (0,255,0),2)

    m = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) 

    if m !=0:
        vx = ((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/m
        vy = ((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/m                

    direct = 'front'
    ratio = 0
    if 0<vx<w and 0<vy<h:
        cv2.circle(img, (int(vx),int(vy)),5,(0,0,255),-1)
        if vx < img_center:
            direct = 'left'
            ratio = (img_center-vx)/img_center
        elif vx > img_center:
            direct = 'right'
            ratio = (vx-img_center)/img_center
    
    return [direct, ratio]

DIRECT_RATIO = ['front', 0]

class Camera(threading.Thread):
    def __init__(self, size):
        threading.Thread.__init__(self)
        self.picam2 = Picamera2()
        self.lsize = size
        
        video_config = self.picam2.create_video_configuration(lores={"size": self.lsize})
        self.picam2.configure(video_config)

    def close(self):
        self.picam2.close()
        cv2.destroyAllWindows()

    def run(self):
        cv2.startWindowThread()
        self.picam2.start()

        while True:
            yuv420 = self.picam2.capture_array("lores")
            frame = cv2.cvtColor(yuv420, cv2.COLOR_YUV420p2RGB)
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            filtered_img = filter_img(frame)
            filtered_img = edge_detection(filtered_img)
            roi = region_of_interest(filtered_img)
            
            # 어느 방향으로 몇 퍼센트 치우쳤는지
            direct, ratio = predict_direct(frame, roi)
            DIRECT_RATIO[0] = direct
            DIRECT_RATIO[1] = ratio

            cv2.imshow("Camera", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.close()