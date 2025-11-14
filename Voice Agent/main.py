from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv
import os, json, datetime

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Twilio config
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
SALON_PHONE = os.getenv("SALON_PHONE")  # optional

class Booking(BaseModel):
    name: str
    date: str
    time: str
    transcript: str = ""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/bookings")
async def create_booking(booking: Booking):
    if not booking.name or not booking.date or not booking.time:
        return JSONResponse({"error": "name, date and time required"}, status_code=400)

    record = {
        "name": booking.name,
        "date": booking.date,
        "time": booking.time,
        "transcript": booking.transcript,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    os.makedirs("data", exist_ok=True)
    bookings_file = "data/bookings.json"
    if os.path.exists(bookings_file):
        with open(bookings_file, "r", encoding="utf-8") as f:
            arr = json.load(f)
    else:
        arr = []

    arr.append(record)
    with open(bookings_file, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2)

    sms_result = None
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM and SALON_PHONE:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                body=f"New booking: {booking.name} on {booking.date} at {booking.time}",
                from_=TWILIO_FROM,
                to=SALON_PHONE
            )
            sms_result = {"sid": msg.sid}
        except Exception as e:
            sms_result = {"error": str(e)}

    return JSONResponse({"ok": True, "booking": record, "sms": sms_result})
