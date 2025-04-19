from typing import Union, Optional
from fastapi import FastAPI, HTTPException
import json
import warnings
from pydantic import BaseModel

# Import CrewAI components
from src.ai_advisor.crew import AiAdvisor
from src.ai_advisor.main import format_result, fillInCourses

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()


class CourseRequest(BaseModel):
    major: str
    semester: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/recommend-courses")
async def recommend_courses(request: CourseRequest):
    """
    API endpoint to get course recommendations based on major and semester
    """
    try:
        # Initialize the CrewAI advisor and run the recommendation
        result = AiAdvisor().crew().kickoff(inputs={
            'major': request.major,
            'semester': request.semester
        })
        
        # Process and format the results
        formatted_result = format_result(result.raw)
        courses = json.loads(formatted_result)
        final_courses = fillInCourses(courses, request.major)
        
        return {
            "major": request.major, 
            "semester": request.semester,
            "courses": final_courses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
