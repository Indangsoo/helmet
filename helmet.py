import RPi.GPIO as GPIO
from api import emergency_call, stuff_call
import time
import asyncio

GPIO.setmode(GPIO.BCM)
# Add setwarnings to False to avoid any warning messages
GPIO.setwarnings(False)

time.sleep(1)

class Button:
  def __init__(self, pin, is_main, stuff_id):
    self.pin = pin
    self.is_pressed = False
    self.is_main = is_main
    self.stuff_id = stuff_id
    self.last_press_time = 0
    self.monitoring = False
    GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    self.start_monitoring()

  def start_monitoring(self):
    import threading
    self.monitoring = True
    self.monitor_thread = threading.Thread(target=self.monitor_button, daemon=True)
    self.monitor_thread.start()

  def stop_monitoring(self):
    self.monitoring = False
    if hasattr(self, 'monitor_thread'):
      self.monitor_thread.join(timeout=1.0)

  def monitor_button(self):
    while self.monitoring:
      if GPIO.input(self.pin) == GPIO.LOW and not self.is_pressed:
        self.handle_press()
      time.sleep(0.05)  # Small delay to prevent CPU hogging

  def call_stuff(self):
    print(f"물건 찾기 {self.stuff_id}") # 물건 찾기 api call
    asyncio.run(stuff_call(self.stuff_id))
    print(f'on {self.stuff_id}')

  def handle_press(self):
    current_time = time.time()
    if (current_time - self.last_press_time) < 1:
      return
    
    self.is_pressed = True
    self.last_press_time = current_time
    time.sleep(0.5)
    
    if self.is_main and GPIO.input(self.pin) == GPIO.LOW:
      print("비상 호출") # 비상 호출 api call
      emergency_call()
    else:
      self.call_stuff()
    
    # Wait for release
    while GPIO.input(self.pin) == GPIO.LOW:
      time.sleep(0.1)
    
    self.is_pressed = False

class UltrasonicWithBuzzer:
  def __init__(self, trigger_pin, echo_pin, buzzer_pin):
    self.echo_pin = echo_pin
    self.buzzer_pin = buzzer_pin
    self.trigger_pin = trigger_pin
    GPIO.setup(self.trigger_pin, GPIO.OUT)
    GPIO.setup(self.echo_pin, GPIO.IN)
    GPIO.setup(self.buzzer_pin, GPIO.OUT)
    

  def get_distance(self):
    GPIO.output(self.trigger_pin, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(self.trigger_pin, GPIO.LOW)

    pulse_start = time.time()
    while GPIO.input(self.echo_pin) == 0:
      pulse_start = time.time()

    while GPIO.input(self.echo_pin) == 1:
      pulse_end = time.time()
    
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    # print(self.trigger_pin, distance)
    return distance
  
  def start_buzzer(self):
    GPIO.output(self.buzzer_pin, GPIO.HIGH)

  def stop_buzzer(self):
    GPIO.output(self.buzzer_pin, GPIO.LOW)

  # play sound by distance like parking sensor
  def play_sound(self, distance):
    if distance < 20:
      self.start_buzzer()
    else:
      self.stop_buzzer()

  def run(self):
    distance = self.get_distance()
    self.play_sound(distance)

ultrasonics = [
  UltrasonicWithBuzzer(17, 27, 22), # left
  UltrasonicWithBuzzer(5, 6, 26), # front
  UltrasonicWithBuzzer(23, 24, 25), # right
]

mainButton = Button(18, True, 0)
stuff1Button = Button(9, False, 1)
stuff2Button = Button(10, False, 2)


try:
  while True:
    for ultrasonic in ultrasonics:
      ultrasonic.run()
      time.sleep(0.1)
except KeyboardInterrupt:
  print("KeyboardInterrupt")
finally:
  mainButton.stop_monitoring()
  stuff1Button.stop_monitoring()
  stuff2Button.stop_monitoring()
  GPIO.cleanup()
