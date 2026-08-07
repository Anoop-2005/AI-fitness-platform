from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import onboarding, plans, habits, sync, coach, photos, admin, trainer, enrich, goal, reports, notifications, subscriptions, body_composition
from services.llm_client import MOCK_MODE

app = FastAPI(title="Iron Ledger", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-fitness-platform-pka9.onrender.com", "http://localhost:5173"],  
    allow_methods=["*"],
    allow_headers=["*"],
)


# Normalize error responses to {"error": "..."} so the frontend can always
# read err.error, regardless of which kind of error FastAPI raised.
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "Invalid request", "detail": exc.errors()})


# Catch-all: any exception we didn't anticipate (a database constraint
# violation, a bug, etc.) still comes back as JSON the frontend can parse,
# instead of a plain-text 500 that would break `await resp.json()` there.
# The real error is logged server-side for debugging; the client only sees
# a generic message.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": "Something went wrong on our end. Please try again."})


app.include_router(onboarding.router)
app.include_router(plans.router)
app.include_router(habits.router)
app.include_router(sync.router)
app.include_router(coach.router)
app.include_router(photos.router)
app.include_router(admin.router)
app.include_router(trainer.router)
app.include_router(enrich.router)
app.include_router(goal.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(subscriptions.router)
app.include_router(body_composition.router)


@app.get("/health")
def health():
    return {"status": "ok", "mock_llm_mode": MOCK_MODE}
