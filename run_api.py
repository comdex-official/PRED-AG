import uvicorn
from prediction_app.api.main import app
from prediction_app.scheduler import start_scheduler
import threading

if __name__ == "__main__":
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Run the API
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    