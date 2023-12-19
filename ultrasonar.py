import RPi.GPIO as GPIO
import threading
import time

DISTANCE = {'left':0, 'front':0, 'right':0}

class UltraSonar(threading.Thread):
    def __init__(self, TRIG, ECHO, name):
        threading.Thread.__init__(self)
        self.TRIG = TRIG
        self.ECHO = ECHO
        self.name = name
        
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        GPIO.output(self.TRIG, GPIO.LOW)

    def dist_check(self):
        count = 0   # ECHO while 갇힘 방지
        GPIO.output(self.TRIG, GPIO.HIGH)
        time.sleep(0.00001)		# 0.00001s = 10 us 
        GPIO.output(self.TRIG, GPIO.LOW)
        
        stop = 0
        start = 0
        
        while GPIO.input(self.ECHO) == GPIO.LOW:
            start = time.time()
            count += 1
            if count > 10000:
                break
        while GPIO.input(self.ECHO) == GPIO.HIGH:
            stop = time.time()
            count = 0

        duration = stop - start

        # 음속 = 340 m/s = 340 * 100 cm/s
        # 왕복 거리이므로 340 * 100 / 2
        distance = (duration * 340 * 100) / 2
        if distance < 5:   # 4cm 이하 값 정확하지 않아 버림
            distance = 4
        elif distance >= 100:
            distance = 100

        return distance

    def interpolation(self):
        dist = []
        while len(dist) < 10:
            dist.append(self.dist_check())
            time.sleep(0.001)
        if len(dist) == 10:
            average_distance = sum(dist) / len(dist)
            dist.pop(0)
            return average_distance

    def run(self):
        try:
            while True:
                average_distance = self.interpolation()
                time.sleep(0.1)
                DISTANCE[threading.currentThread().getName()] = average_distance
        except KeyboardInterrupt:
            self.join()