class Semester:
    """A single semester"""

    def __init__(self, year, semester):
        self.semester = semester
        self.year = year
        self.year_short = year[2:4]
                
        self.update_other_semeseter_parameters()


    def __str__(self):
        return '{}{}'.format(self.semester_short, self.year_short)


    def __repr__(self):
        return '{}{}'.format(self.semester_short, self.year_short)


    def update_other_semeseter_parameters(self):
        """Set the other parameters for the semester"""

        if self.semester == "Spring":
            self.semester_short = "Sp"
            self.semester_sort = "1"
        elif self.semester == "Summer":
            self.semester_short = "Su"
            self.semester_sort = "2"
        elif self.semester == "Fall":
            self.semester_short = "F"
            self.semester_sort = "3"
    

    def update_year(self, year):
        """Update the year. Automatically expands to 4 digit year as necessary"""
        
        if len(year) == 2:
            self.year = "20"
        self.year += year
        self.year_short = self.year[2:4]


    def update_semester(self, semester):
        """"Update the semester. Automatically expands to full name if necessary"""

        # if there is just 1 character, then it's likely fall.
        if len(semester) == 1 and semester[0] == "F":
            self.semester = "Fall"
        # if there's 2 characters, then we'll need to determine if it's spring or summer
        elif len(semester) == 2 and semester[0] == "S":
            if semester[1] == "P":
                self.semester = "Spring"
            elif semester[1] == "U":
                self.semester = "Summer"
        
        # Update the other parameters
        self.update_other_semeseter_parameters()
        