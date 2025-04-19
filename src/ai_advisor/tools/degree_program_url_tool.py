import os
import pandas as pd
from difflib import get_close_matches
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field

class DegreeProgramUrlQueryInput(BaseModel):
    degree_program: str = Field(..., description="The degree program to search for.")

class DegreeProgramUrlTool(BaseTool):
    name: str = "Degree Program URL Finder"
    description: str = "Find the plan of study URL for a given degree program"
    args_schema: Type[BaseModel] = DegreeProgramUrlQueryInput
    csv_path: str = Field(default="")

    def __init__(self, **data):
        super().__init__(**data)
        self.csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "knowledge",
            "degree_programs.csv"
        )

    def _run(self, degree_program: str) -> str:
        # Get the full plan of study for the given major
        print(f"Getting url for {degree_program}")
        url = self._get_plan_of_study_url(degree_program)
        
        if not url:
            return {"url": "", "message": f"No url found for the degree program: {degree_program}"}
        
        # Return empty list if no courses found for the specific semester
        return {"url": url, "message": f"Found url for {degree_program}"}
            
        
    def _get_plan_of_study_url(self, degree_program):
        """
        Find the closest matching degree program and return its plan of study URL.
        
        Args:
            degree_program (str): The degree program to search for.
            
        Returns:
            str: The URL to the plan of study for the closest matching degree program.
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.csv_path)
            
            # Check if required columns exist
            if 'degree_program' not in df.columns or 'plan_of_study_url' not in df.columns:
                return "Error: CSV file does not contain required columns."
            
            # Get all degree programs
            degree_programs = df['degree_program'].tolist()
            
            # Find closest match
            matches = get_close_matches(degree_program, degree_programs, n=1, cutoff=0.6)
            print(f"Matches: {matches}")
            if not matches:
                return None
                
            best_match = matches[0]
            
            # Get the URL for the best match
            url = df[df['degree_program'] == best_match]['plan_of_study_url'].iloc[0]
            
            print(f"Found url for {degree_program}: {url}")
            return url
            
        except Exception as e:
            return f"Error finding degree program: {str(e)}"

