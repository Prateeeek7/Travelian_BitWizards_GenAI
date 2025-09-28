from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Budget parsing function
def parse_budget(budget_string: str, duration: int) -> dict:
    """
    Parse budget string and calculate detailed budget breakdown.
    
    Args:
        budget_string: Budget string from frontend (e.g., "Luxury (₹25,000 - ₹50,000)")
        duration: Trip duration in days
        
    Returns:
        dict: Budget breakdown with total, daily, and category amounts
    """
    # Extract budget range from string
    if "Budget (Under ₹10,000)" in budget_string:
        total_budget = 8000  # Use lower end for budget
    elif "Moderate (₹10,000 - ₹25,000)" in budget_string:
        total_budget = 18000  # Use middle range for moderate
    elif "Luxury (₹25,000 - ₹50,000)" in budget_string:
        total_budget = 40000  # Use upper-middle for luxury
    elif "Premium (Above ₹50,000)" in budget_string:
        total_budget = 75000  # Use higher amount for premium
    else:
        total_budget = 15000  # Default fallback
    
    # Calculate daily budget
    daily_budget = total_budget // duration if duration > 0 else total_budget
    
    # Budget breakdown percentages (typical travel spending)
    breakdown = {
        'total_budget': total_budget,
        'daily_budget': daily_budget,
        'accommodation': int(total_budget * 0.35),  # 35% for accommodation
        'food': int(total_budget * 0.25),          # 25% for food
        'transport': int(total_budget * 0.20),     # 20% for transport
        'activities': int(total_budget * 0.15),    # 15% for activities
        'shopping': int(total_budget * 0.05)       # 5% for shopping
    }
    
    return breakdown

# Add the current directory to path to import travel module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from travel import (
        destination_research_task, accommodation_task, transportation_task,
        activities_task, dining_task, itinerary_task, chatbot_task,
        run_task
    )
    TRAVEL_MODULE_AVAILABLE = True
except ImportError:
    TRAVEL_MODULE_AVAILABLE = False
    print("Travel module not available")

# Initialize FastAPI app
app = FastAPI(
    title="Travelian API",
    description="AI-powered travel planning API for India",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TravelRequest(BaseModel):
    origin: str
    destination: str
    startDate: str
    endDate: str
    duration: int
    budget: str
    travelStyle: str
    interests: List[str]
    specialRequirements: Optional[str] = ""

class TravelResponse(BaseModel):
    itinerary: str
    mapUrl: Optional[str] = None
    budget: Optional[dict] = None

class ChatbotRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatbotResponse(BaseModel):
    response: str
    history: List[Dict[str, str]]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    travel_module: bool
    chatbot_module: bool
    version: str
    uptime: float
    environment: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        travel_module=TRAVEL_MODULE_AVAILABLE,
        chatbot_module=TRAVEL_MODULE_AVAILABLE,
        version="1.0.0",
        uptime=0.0,  # This would be calculated in a real app
        environment="development"
    )

# Travel planning endpoint
@app.post("/travel/plan", response_model=TravelResponse)
async def plan_travel(request: TravelRequest):
    if not TRAVEL_MODULE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Travel module not available")
    
    try:
        # Create travel context
        travel_context = {
            "origin": request.origin,
            "destination": request.destination,
            "start_date": request.startDate,
            "end_date": request.endDate,
            "duration": request.duration,
            "budget": request.budget,
            "travel_style": request.travelStyle,
            "interests": request.interests,
            "special_requirements": request.specialRequirements or ""
        }
        
        # Parse and calculate budget amounts
        budget_info = parse_budget(request.budget, request.duration)
        
        # Create input context string with detailed budget information
        input_context = (
            f"Travel Request Details:\n"
            f"Origin: {request.origin}\n"
            f"Destination: {request.destination}\n"
            f"Duration: {request.duration} days\n"
            f"Budget Level: {request.budget}\n"
            f"Total Budget: ₹{budget_info['total_budget']:,}\n"
            f"Daily Budget: ₹{budget_info['daily_budget']:,}\n"
            f"Budget Breakdown: Accommodation ₹{budget_info['accommodation']:,}, Food ₹{budget_info['food']:,}, Transport ₹{budget_info['transport']:,}, Activities ₹{budget_info['activities']:,}\n"
            f"Travel Style: {request.travelStyle}\n"
            f"Preferences/Interests: {', '.join(request.interests)}\n"
            f"Special Requirements: {request.specialRequirements}\n"
        )
        
        # Run travel planning tasks
        tasks = [
            destination_research_task,
            accommodation_task,
            transportation_task,
            activities_task,
            dining_task,
            itinerary_task
        ]
        
        results = {}
        api_key = os.getenv("GEMINI_API_KEY")
        for task in tasks:
            try:
                # Create enhanced context with budget information for each task
                enhanced_context = input_context
                if hasattr(task, 'description') and 'budget' in task.description:
                    enhanced_context += f"\n\nBUDGET DETAILS FOR THIS TASK:\n"
                    enhanced_context += f"Budget Level: {request.budget}\n"
                    enhanced_context += f"Total Budget: ₹{budget_info['total_budget']:,}\n"
                    enhanced_context += f"Daily Budget: ₹{budget_info['daily_budget']:,}\n"
                    enhanced_context += f"Accommodation Budget: ₹{budget_info['accommodation']:,}\n"
                    enhanced_context += f"Food Budget: ₹{budget_info['food']:,}\n"
                    enhanced_context += f"Transport Budget: ₹{budget_info['transport']:,}\n"
                    enhanced_context += f"Activities Budget: ₹{budget_info['activities']:,}\n"
                
                result = run_task(task, enhanced_context, api_key)
                key = task.description[:30]
                results[key] = result
                print(f"Task completed: {key}")
            except Exception as e:
                key = task.description[:30]
                print(f"Error in {key}: {e}")
                results[key] = f"Error: {str(e)}"
        
        # Generate final itinerary
        itinerary = results.get('Create a day-by-day itinerary', 'Unable to generate itinerary')
        if itinerary == 'Unable to generate itinerary':
            # Try alternative key
            itinerary = results.get('Create a day-by-day itinerary', 'Unable to generate itinerary')
            # If still not found, get the last result (itinerary task should be last)
            if itinerary == 'Unable to generate itinerary' and results:
                itinerary = list(results.values())[-1]
        
        # Generate map data for frontend to handle
        map_data = {
            "origin": request.origin,
            "destination": request.destination,
            "type": "directions"
        }
        
        return TravelResponse(
            itinerary=itinerary,
            mapUrl=json.dumps(map_data),
            budget=budget_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning travel: {str(e)}")

# Chatbot endpoint
@app.post("/chatbot/ask", response_model=ChatbotResponse)
async def ask_chatbot(request: ChatbotRequest):
    if not TRAVEL_MODULE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Chatbot module not available")
    
    try:
        # Create chat context
        chat_context = {
            "message": request.message,
            "history": request.history or []
        }
        
        # Run chatbot task
        api_key = os.getenv("GEMINI_API_KEY")
        response = run_task(chatbot_task, request.message, api_key)
        
        # Update history
        new_history = request.history.copy() if request.history else []
        new_history.append({"role": "user", "content": request.message})
        new_history.append({"role": "assistant", "content": response})
        
        return ChatbotResponse(
            response=response,
            history=new_history
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chatbot request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



