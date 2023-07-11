# import Flask and other libraries
from tools.scheduler import scheduler
from context.context import app


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    with app.app_context():
        scheduler.start()