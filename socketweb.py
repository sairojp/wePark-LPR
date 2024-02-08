import socketio
import sys
sio = socketio.Client()





@sio.event 
def connect():
  print('connection established')

  

@sio.event 
def connect_error(data):
  print("The connection failed")

@sio.event
def disconnect():
  print("disconnected")


@sio.event
def my_message(data):
    print('message received with ', data)
    




    
def main():
  sio.connect("http://localhost:3002")

  
  sio.wait()

main()

