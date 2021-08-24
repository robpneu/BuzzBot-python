import re, logging
from semester import Semester

class Course:
    """A single course"""

    def __init__(self, course_string : str, current_year = "", current_semester = ""):
        self.raw_string = course_string # The raw string to make the course
        self.is_possible = False # if this course is even possible (ie is the course_string formatted correctly). default to false
        self.is_special_topic = False # if this is a special topics course. default to false
        self.dept = ""
        self.code = ""
        self.topic = "0"
        self.title = ""
        
        # assume the current year and semester
        self.semester = Semester(current_year, current_semester)

        # separate each component of a course, indicated by dashes (dept####-semester## or dept####-TOPIC-semester##)
        course_components = course_string.split('-')

        # if there is at least 1 component, then process it
        if len(course_components) > 0:

            # Use a regex to the department and course code from the first entry in course_components
            dept_course = re.findall(r'\d+|\D+', course_components[0])

            # if there is a department and a course, then the length will be 2. otherwise this is not possibly valid
            if len(dept_course) == 2:
                # Get rid of any hanging white space with strip.
                self.dept = dept_course[0].strip().upper()
                self.code = dept_course[1].strip()
                self.topic = "0" # default to 0
                self.is_possible = True

            # If there are 2 course components, then there is either a special topic or a semester. This will figure out which.
            if len(course_components) == 2:
                # split the course components based on digits and non-digits.
                course_component = re.findall(r'\d+|\D+', course_components[1])

                # if the number of components in the second portion is 1, then it is a topic (no digits)
                if len(course_component) == 1:
                    self.topic = course_component[0].upper() # get the topic and make it all caps
                    self.is_special_topic = True # This is a special topics course

                # if the number of components in the second portion is 2, then it is a semester and year
                elif len(course_component) == 2:
                    self.semester.update_semester(course_component[0])
                    self.semester.update_year(course_component[1])

            # If there are 3 course components, then there is a special topic and semester as well
            elif len(course_components) == 3:
                self.topic = course_components[1].upper() # topic will always be in the second position. Make it all caps
                self.is_special_topic = True # This is a special topics course
                
                # split the semester and year, which will always be in the third position
                semester_year = re.findall(r'\d+|\D+', course_components[2])
                self.semester.update_semester(semester_year[0]) # update the semester
                self.semester.update_year(semester_year[1]) # update the year

    def __str__(self):
        if self.is_special_topic:
            return '{}{}-{}-{}'.format(self.dept, self.code, self.topic, self.semester)
        else:
            return '{}{}-{}'.format(self.dept, self.code, self.topic, self.semester)

    def __repr__(self):
        return '{}{}-{}-{}'.format(self.dept, self.code, self.topic, self.semester)

    def set_title(self, new_title):
        """Set the course title"""

        # Set the title and remove any hanging whitespace
        self.title = new_title.strip()

    
    def get_full_name(self):
        """Get the full name for the course.
            Will be in the format:
                DEPT CODE-Topic or
                DEPT CODE if there is not topic"""
        if self.is_special_topic:
            return '{} {}-{}'.format(self.dept, self.code, self.topic)
        else:
            return '{} {}'.format(self.dept, self.code)

    def get_full_semester(self):
        """Get the full name for semester the course is in.
            Will be in the format:
                SEMESTER YEAR"""
        return '{} {}'.format(self.semester.semester, self.semester.year)

    def get_short_semester(self):
        """Get the short name for semester the course is in.
            Will be in the format:
                SemYr"""
        return '{} {}'.format(self.semester.semester_short, self.semester.year_short)

    def get_full_name_and_semester(self):
        """Get the full name for the course.
            Will be in the format:
                DEPT CODE-Topic SemYr"""
        return '{} {}'.format(self.get_full_name(), self.get_short_semester())

    def get_category_name(self):
        """Get the name for the category.
            Will be in the format:
                DEPT CODE (SEM'YR) - Title"""
        return '{} {} ({}\'{}) - {}'.format(self.dept, self.code, self.semester.semester_short, self.semester.year_short, self.title)
    
    def get_channel_postfix_name(self):
        """Get the name to append to a channel name.
            Will be in the format:
                -deptCode-semYR"""
        return '-{}{}-{}{}'.format(self.dept, self.code, self.semester.semester_short, self.semester.year_short)

    def get_course_and_title(self):
        """Get the course in the format:
                DEPT CODE \"Title\" or
                DEPT CODE-TOPIC \"Title\""""
        return '{} \"{}\"'.format(self.get_full_name().upper(), self.title)