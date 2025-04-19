#!/usr/bin/env python
import json
import sys
import warnings
from datetime import datetime
import csv
import os
import random

# Import both approaches
from src.ai_advisor.crew import AiAdvisor  # Original CrewAI approach

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def format_result(result):
    """Clean up result by removing markdown code block delimiters if present."""
    if isinstance(result, str):
        # Remove markdown code block formatting if present
        if result.startswith("```") and result.endswith("```"):
            # Find the first newline to skip the ```json line
            first_newline = result.find("\n")
            if first_newline != -1:
                # Remove opening ```json and closing ```
                result = result[first_newline+1:-3].strip()
    
    return result

def fillInCourses(result, major):
    """
    Fill in the courses for the major by looking up details from the courses.csv file.
    For generic course types (Elective, STEM, etc.), select a random matching course.
    """
    # Get the root directory path
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    courses_csv_path = os.path.join(root_dir, 'knowledge', 'courses.csv')
    
    # Load courses from CSV by fulfillment type
    courses_by_type = {
        'Elective': [],
        'STEM Cognate': [],
        'Language': [],
        'People and Society Cognate': [],
        'Arts and Humanities Cognate': []
    }
    
    with open(courses_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fulfillment = row['fullfillment_type'].strip()
            if fulfillment in courses_by_type:
                courses_by_type[fulfillment].append(row)
    
    courses = []
    try:
        for course in result:
            print(course)
            
            # Try to get course code with different key names
            try:
                course_code = course.get('code', '')
                if not course_code:
                    course_code = course.get('course_code', '')
            except KeyError:
                # If any other KeyError occurs
                course_code = ''
            
            # Handle generic course types by selecting a random matching course
            if 'Elective' in course_code:
                if courses_by_type['Elective']:
                    random_course = random.choice(courses_by_type['Elective'])
                    courses.append({
                        'code': random_course['course_code'],
                        'name': random_course['course_name'],
                        'description': random_course['description'],
                        'credits': random_course['credits'],
                        'fulfillment_type': random_course['fullfillment_type']
                    })
            elif 'STEM' in course_code:
                if courses_by_type['STEM Cognate']:
                    random_course = random.choice(courses_by_type['STEM Cognate'])
                    courses.append({
                        'code': random_course['course_code'],
                        'name': random_course['course_name'],
                        'description': random_course['description'],
                        'credits': random_course['credits'],
                        'fulfillment_type': random_course['fullfillment_type']
                    })
            elif 'Language' in course_code:
                if courses_by_type['Language']:
                    random_course = random.choice(courses_by_type['Language'])
                    courses.append({
                        'code': random_course['course_code'],
                        'name': random_course['course_name'],
                        'description': random_course['description'],
                        'credits': random_course['credits'],
                        'fulfillment_type': random_course['fullfillment_type']
                    })
            elif 'People and Society' in course_code:
                if courses_by_type['People and Society Cognate']:
                    random_course = random.choice(courses_by_type['People and Society Cognate'])
                    courses.append({
                        'code': random_course['course_code'],
                        'name': random_course['course_name'],
                        'description': random_course['description'],
                        'credits': random_course['credits'],
                        'fulfillment_type': random_course['fullfillment_type']
                    })
            elif 'Arts and Humanities' in course_code:
                if courses_by_type['Arts and Humanities Cognate']:
                    random_course = random.choice(courses_by_type['Arts and Humanities Cognate'])
                    courses.append({
                        'code': random_course['course_code'],
                        'name': random_course['course_name'],
                        'description': random_course['description'],
                        'credits': random_course['credits'],
                        'fulfillment_type': random_course['fullfillment_type']
                    })
            else:
                # Include specific courses as they are but ensure consistent field names
                processed_course = {}
                
                # Handle code/course_code consistency
                if 'code' in course:
                    processed_course['code'] = course['code']
                elif 'course_code' in course:
                    processed_course['code'] = course['course_code']
                
                # Handle name/course_name consistency
                if 'name' in course:
                    processed_course['name'] = course['name']
                elif 'course_name' in course:
                    processed_course['name'] = course['course_name']
                
                # Handle description
                if 'description' in course:
                    processed_course['description'] = course['description']
                
                # Handle credits and ensure it's a string
                if 'credits' in course:
                    processed_course['credits'] = str(course['credits'])
                
                # Handle optional fields
                if 'fulfillment_type' in course:
                    processed_course['fulfillment_type'] = course['fulfillment_type']
                if 'prerequisites' in course:
                    processed_course['prerequisites'] = course['prerequisites']
                
                courses.append(processed_course)
        
        return courses
    except KeyError as e:
        print(f"KeyError occurred: {e}")
        return []

def run():
    """
    Run the original CrewAI-based approach but with a student query.
    """
    major = "B.S. in Computer Science"
    semester = "3"
    
    try:
        
        result = AiAdvisor().crew().kickoff(inputs={
            'major': major,
            'semester': semester
        })
        
        print("\nRecommendation Results:")
        # print(format_result(result))
        formatted_result = format_result(result.raw)
        courses = json.loads(formatted_result)
        final_courses = fillInCourses(courses, major)
        print(final_courses)
        
    except Exception as e:
        raise Exception(f"An error occurred while processing the query: {e}")

if __name__ == "__main__":
    run()