from fastapi import APIRouter
from . import weight, blood_pressure, exercise, heart_rate, height, doctor_visit, dietary_goals

router = APIRouter()

# Include all health-related routers
router.include_router(weight.router, prefix="/weight", tags=["Health - Weight"])
router.include_router(blood_pressure.router, prefix="/blood-pressure", tags=["Health - Blood Pressure"])
router.include_router(exercise.router, prefix="/exercise", tags=["Health - Exercise"])
router.include_router(heart_rate.router, prefix="/heart-rate", tags=["Health - Heart Rate"])
router.include_router(height.router, prefix="/height", tags=["Health - Height"])
router.include_router(doctor_visit.router, prefix="/doctor-visits", tags=["Health - Doctor Visits"])
router.include_router(dietary_goals.router, prefix="/dietary-goals", tags=["Health - Dietary Goals"]) 