import RPi.GPIO as GPIO
import time

from motor import *
from ultrasonar import UltraSonar, DISTANCE
from camera import Camera, DIRECT_RATIO

GPIO.setmode(GPIO.BCM)

# PIN 설정
## left motor 핀넘버
EN1 = 13
IN1 = 19
IN2 = 26
## right motor 핀넘버
EN2 = 12
IN3 = 5
IN4 = 6

## ultra sonar 핀넘버
### left ultra sonar
TRIG1 = 17
ECHO1 = 27
### front ultra sonar
TRIG2 = 22
ECHO2 = 23
### right ultra sonar
TRIG3 = 2
ECHO3 = 3

TRIG = [TRIG1, TRIG2, TRIG3]
ECHO = [ECHO1, ECHO2, ECHO3]
ULTRASONAR = ['left','front', 'right']

# speed limitpython
limit_HIGH = 60      # 속도 제한
limit_LOW = 35      # 속도 제한
turn_speed = (limit_HIGH + limit_LOW)//2

def car_forward(R_motor, L_motor, speed_R = limit_LOW, speed_L = limit_LOW):
    print("forward")
    R_motor.forward(speed_R)
    L_motor.forward(speed_L)    
def car_backward(R_motor, L_motor, speed_R = limit_HIGH, speed_L = limit_HIGH):
    print("backward")
    R_motor.backward(speed_R)
    L_motor.backward(speed_L) 
    #time.sleep(1)   
def car_Turn_CCW(R_motor, L_motor, speed = turn_speed):
    print("CCW, left")
    R_motor.forward(speed+10)
    L_motor.backward(speed-10)
    # time.sleep(1)
def car_Turn_CW(R_motor, L_motor, speed = turn_speed):
    print("CW, right")
    R_motor.backward(speed-10)
    L_motor.forward(speed+10)
    #time.sleep(1)
def car_Stop(R_motor, L_motor):
    print("Stop")
    R_motor.stop()
    L_motor.stop()

if __name__ == '__main__':    
    # Init    
    l_motor = Motor(EN1, IN1, IN2)
    r_motor = Motor(EN2, IN3, IN4)
    speed_R = 0
    speed_L = 0    

# 카메라 작동
    camera = Camera(size=(320, 240))
    camera.start()
    time.sleep(5)

    car_Stop(r_motor, l_motor)
    car_forward(r_motor, l_motor, limit_HIGH, limit_HIGH)
    time.sleep(0.1)       # 전력 공급 안정화
    for i in range(3):
        ultrasonar = UltraSonar(TRIG[i], ECHO[i], name=ULTRASONAR[i])
        ultrasonar.start()    
    time.sleep(1)       # 초음파 센서 값 읽어오는데 시간 
    print('start')

    try:
        while True:
            front = DISTANCE['front']
            right = DISTANCE['right']
            left  = DISTANCE['left']
            print('\n{:.1f}, {:.1f}, {:.1f}'.format(front, right, left))

            camera_direct = DIRECT_RATIO[0]
            direct_ratio = DIRECT_RATIO[1]
            print('direct: {} ratio: {:.1f}%%'.format(camera_direct, direct_ratio*100))

            obstacle=30
            term = 5
            # 운전
            if front<=obstacle+term:
                print("front")
                while DISTANCE['front']<=obstacle-term:  
                    print('s {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                    car_backward(r_motor, l_motor)

                if left < obstacle+term and (camera_direct=='left' and direct_ratio > 0.6):                    
                    while DISTANCE['front']<obstacle+term and DISTANCE['right']-DISTANCE['left'] < obstacle-term:
                        print('s {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                        car_Turn_CW(r_motor, l_motor)
                    
                elif right < obstacle+term and (camera_direct=='right' and direct_ratio > 0.6):
                    while  DISTANCE['front']<obstacle+term and DISTANCE['left']-DISTANCE['right']<obstacle-term:
                        print('s {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                        car_Turn_CCW(r_motor, l_motor)
                          

            if left<obstacle+term and (camera_direct=='left' and direct_ratio > 0.6):
                print("left, turn right")          
                while DISTANCE['front']<obstacle-term:     
                    print('s {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                    car_backward(r_motor, l_motor)
                
                while DISTANCE['front']<obstacle+term and DISTANCE['right']-DISTANCE['left'] < obstacle-term:
                    print('big {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                    car_Turn_CW(r_motor, l_motor)
               

            if right<obstacle+term and (camera_direct=='right' and direct_ratio > 0.6):
                print("right, turn left")
                while DISTANCE['front']<obstacle-term:     
                    print('s {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                    car_backward(r_motor, l_motor)
                   
                while DISTANCE['front']<obstacle+term and DISTANCE['left']-DISTANCE['right']<obstacle-term:
                    print('big {:.1f}, {:.1f}, {:.1f}'.format(front, right, left))
                    car_Turn_CCW(r_motor, l_motor)            
        
            car_forward(r_motor, l_motor)

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

GPIO.cleanup()
