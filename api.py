import requests
import time
import asyncio
import websockets

# send get request to emergency call api : http://59.187.251.226:54549/indoor/danger?key=시간
def emergency_call():
  current_time = time.time()
  requests.get(f"http://59.187.251.226:54549/indoor/danger?key={current_time}")

async def stuff_call(stuff_id):
  print('here')
  ws_app = await websockets.connect("ws://192.168.2.14:8765")
  print('connected')
  try:
      await ws_app.send(f'on {stuff_id}')
  except:
      print("error")
