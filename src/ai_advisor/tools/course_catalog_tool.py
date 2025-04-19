import logging
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import re
import traceback

# Set up logger
logger = logging.getLogger(__name__)

class CourseCatalogQueryInput(BaseModel):
    """Input schema for CourseCatalogTool."""
    major: str = Field(..., description="Student's major (e.g., 'Computer Science')")
    semester: int = Field(..., description="Current or upcoming semester number")
    url: str = Field(..., description="The URL to the plan of study page")
    
class CourseCatalogTool(BaseTool):
    name: str = "Course Catalog Tool"
    description: str = (
        "Queries the university course catalog to find available courses for a given major and semester."
    )
    args_schema: Type[BaseModel] = CourseCatalogQueryInput

    def _run(self, major: str, semester: int, url: str) -> str:
        # Get the full plan of study for the given major
        logger.info(f"Getting plan of study for {major} from URL: {url}")
        plan_of_study = self._get_suggested_plan_of_study(major, url)
        
        if not plan_of_study:
            logger.warning(f"No plan of study found for the major: {major}")
            return {"courses": [], "message": f"No plan of study found for the major: {major}"}
        
        # Convert semester number to year and term
        year = (semester + 1) // 2  # Semesters 1-2 = Year 1, 3-4 = Year 2, etc.
        term = "Fall" if semester % 2 == 1 else "Spring"
        
        logger.info(f"Looking for courses in Year {year}, {term} semester")
        
        # Find the relevant semester in the plan of study
        for semester_plan in plan_of_study:
            if semester_plan["year"] == year and semester_plan["semester"] == term:
                logger.info(f"Found {len(semester_plan['courses'])} courses for {major}, Year {year} {term}")
                return {
                    "courses": semester_plan["courses"],
                    "message": f"Found courses for {major}, Year {year} {term}"
                }
        
        # Return empty list if no courses found for the specific semester
        logger.warning(f"No courses found for {major}, Year {year} {term}")
        return {"courses": [], "message": f"No courses found for {major}, Year {year} {term}"}
    
    def _get_suggested_plan_of_study(self, major: str, url: str) -> List[Dict[str, Any]]:
        """Get the suggested plan of study for a given major.
        
        Args:
            major: The student's major (e.g., 'Computer Science')
        
        Returns:
            A list of dictionaries containing course information organized by year and semester
        """
        logger.info(f"Getting suggested plan of study for {major} from URL: {url}")
        
        try:
            # Make GET request to the course catalog
            logger.warning(f"Making GET request to {url}#planofstudytext")
            response = requests.get(url + "#planofstudytext")
            response.raise_for_status()
            
            # Parse the HTML content
            logger.warning("Parsing HTML content")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the plan of study table
            logger.warning("Looking for plan of study table")
            plan_table = soup.select_one('#planofstudytextcontainer table.sc_plangrid')
            if not plan_table:
                logger.warning(f"No plan of study table found at URL: {url}")
                return []
            
            logger.info("Found plan of study table, extracting course information")
            plan_of_study = []
            current_year = None
            current_semester = None
            courses = []
            
            row_count = 0
            for row in plan_table.find_all('tr'):
                row_count += 1
                # Check if this is a year row
                if 'plangridyear' in row.get('class', []):
                    if current_year and current_semester and courses:
                        # Save previous semester data before starting a new year
                        plan_of_study.append({
                            "year": current_year,
                            "semester": current_semester,
                            "courses": courses
                        })
                        logger.warning(f"Saved {len(courses)} courses for Year {current_year}, {current_semester}")
                        courses = []
                    
                    year_text = row.text.strip()
                    logger.warning(f"Found year row: {year_text}")
                    if 'Year One' or 'Freshman Year' in year_text:
                        current_year = 1
                    elif 'Year Two' or 'Sophomore Year' in year_text:
                        current_year = 2
                    elif 'Year Three' or 'Junior Year' in year_text:
                        current_year = 3
                    elif 'Year Four' or 'Senior Year' in year_text:
                        current_year = 4
                    
                # Check if this is a semester row
                elif 'plangridterm' in row.get('class', []):
                    if current_year and current_semester and courses:
                        # Save previous semester data before starting a new semester
                        plan_of_study.append({
                            "year": current_year,
                            "semester": current_semester,
                            "courses": courses
                        })
                        logger.warning(f"Saved {len(courses)} courses for Year {current_year}, {current_semester}")
                        courses = []
                    
                    semester_text = row.text.strip()
                    logger.warning(f"Found semester row: {semester_text}")
                    if 'Fall' in semester_text:
                        current_semester = 'Fall'
                    elif 'Spring' in semester_text:
                        current_semester = 'Spring'
                
                # Check if this is a course row (not a header, sum or total row)
                elif (row.find('td', class_='codecol') and 
                      'plangridsum' not in row.get('class', []) and 
                      'plangridtotal' not in row.get('class', [])):
                    
                    logger.warning(f"Processing course row {row_count}")
                    code_cell = row.find('td', class_='codecol')
                    title_cell = row.find('td', class_='titlecol')
                    hours_cell = row.find('td', class_='hourscol')
                    
                    # Extract course code
                    course_code = ""
                    if code_cell:
                        # Check if there's a link in the codecol
                        course_link = code_cell.find('a')
                        if course_link:
                            course_code = course_link.text.strip()
                        else:
                            # Handle cases like "Elective" or "Language Course"
                            comment = code_cell.find('span', class_='comment')
                            if comment:
                                course_code = comment.text.strip()
                    
                    # Extract course name
                    course_name = ""
                    if title_cell:
                        course_name = title_cell.text.strip()
                    elif code_cell and not course_code:
                        # For cases where course name is in the codecol
                        course_name = code_cell.text.strip()
                    
                    # Extract credit hours
                    credit_hours = ""
                    if hours_cell:
                        credit_hours = hours_cell.text.strip()
                    
                    if (course_code or course_name) and current_year and current_semester:
                        logger.warning(f"Added course: {course_code} - {course_name} ({credit_hours} credit hours)")
                        courses.append({
                            "course_code": course_code,
                            "course_name": course_name,
                            "credit_hours": credit_hours
                        })
            
            # Add the last semester's courses
            if current_year and current_semester and courses:
                plan_of_study.append({
                    "year": current_year,
                    "semester": current_semester,
                    "courses": courses
                })
                logger.warning(f"Saved final set of {len(courses)} courses for Year {current_year}, {current_semester}")
            else:
                logger.warning(f"fuckkk youuuu")
                if not current_year:
                    logger.warning(f"no current year")
                if not current_semester:
                    logger.warning(f"no current semester")
                if not courses:
                    logger.warning(f"no courses")

            logger.info(f"Extracted plan of study with {len(plan_of_study)} semesters")
            
            # Log a summary of what we found
            for semester in plan_of_study:
                logger.info(f"Year {semester['year']} {semester['semester']}: {len(semester['courses'])} courses")
            
            return plan_of_study
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching plan of study: {str(e)}")
            logger.warning(traceback.format_exc())
            return []
        except Exception as e:
            # Log the error and return empty list
            logger.error(f"Error fetching plan of study: {str(e)}")
            logger.warning(traceback.format_exc())
            return []
    
    