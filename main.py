# import Flask and other libraries
from context.context import app
from context.sockets import socketio


#Run the app on port 5000
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)