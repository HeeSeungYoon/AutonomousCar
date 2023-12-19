import RPi.GPIO as GPIO

# 속도 증감 정도 조절 가능
ACC = 5
DEC = 5

class Motor:
    # 모터 초기화
    def __init__(self, en, in1, in2):
        self.en = en
        self.in1 = in1
        self.in2 = in2
        self.speed = 0
        GPIO.setup(self.en, GPIO.OUT)
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        
        self.pwm = GPIO.PWM(self.en, 1000)
        self.pwm.start(self.speed)

    # 앞으로 동작, 속도는 30%
    def forward(self, speed = 30):
        self.pwm.ChangeDutyCycle(speed)
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)

    # 뒤로 동작, 속도는 30%
    def backward(self, speed = 30):
        self.speed = 30
        self.pwm.ChangeDutyCycle(self.speed)
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)

    # 브레이크
    def stop(self):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.HIGH)

    # 속도 증가
    def speedUp(self):
        self.speed += ACC
        self.pwm.ChangeDutyCycle(self.speed)

    # 속도 감소
    def speedDown(self):
        self.speed -= DEC
        self.pwm.ChangeDutyCycle(self.speed)

    # 모터(pwm) 종료
    def exit(self):
        self.pwm.stop()