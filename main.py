# import Flask and other libraries
from tools.scheduler import scheduler
from context.context import app

import sys
import io

# class MultiStream:
#     def __init__(self, streams):
#         self.streams = streams

#     def write(self, message):
#         for stream in self.streams:
#             try:
#                 stream.write(message)
#                 stream.flush()
#             except Exception as e:
#                 print(e)

#     def flush(self):
#         pass

#     def __del__(self):
#         for stream in self.streams:
#             if hasattr(stream, "close"):
#                 stream.close()

# console_out = sys.stdout

# with open('log.txt', 'w') as file_out:
#     file_out = io.TextIOWrapper(file_out)
#     sys.stdout = MultiStream([console_out, file_out])


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    scheduler.start()