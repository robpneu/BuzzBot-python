import discord
from course import Course

class DiscordMessage:
    """A single message in progress"""

    def __init__(self):
        self.message = ""

    def append(self, msg : str):
        """Append the string to a new line"""
        # If the message is currently blank, just set it to the string
        if self.message == "":
            self.message = msg

        # if the message is not currently blank, add a new line and then append the string
        else:
            self.message += "\n" + msg

    def append_course_added(self, course : Course, prefix = ""):
        """Append the "you have been added to this course" message"""
        
        line = prefix # start with any prefix provided
        line += 'You have been added to {} in the {} semester.'.format(course.get_full_name(), course.get_full_semester())
        self.append(line)

    def append_course_requested(self, course : Course):
        """Append the "you have successfully requested this course" message"""

        line = 'You are the first person to request {} in the {} semester. '.format(course.get_full_name(), course.get_full_semester())
        line += "Once there is another request for it, I will create a group and automatically add you to it."
        self.append(line)

    def append_course_already_requested(self, course : Course):
        """Append the "you have already requested this course" message"""
        
        line = 'You have already requested {} in the {} semester. '.format(course.get_full_name(), course.get_full_semester())
        line += "Don't worry, I haven't forgotten :smiley:! Once there is another request for it, I will create a group and automatically add you to it."
        self.append(line)
    
    def append_course_previously_requested_added(self, course : Course, prefix : str):
        """Append the "you had previously requested this course that I just created and I've added you to it" message"""

        line = prefix # start with the prefix provided
        line += 'You had previously requested {} in the {} semester '.format(course.get_full_name(), course.get_full_semester())
        line += "so you have been added to it automatically."
        self.append(line)

    def append_course_unknown_topic(self, course : Course):
        """Append the "this is a special topics course but I don't recognize the topic specified" message"""

        line = '{} {} is a special topics course but I didn\'t recognize the topic you specified.'.format(course.dept, course.code)
        line += "\nThe topic is the first 3 letters of the course name and should be included after the course number with a dash. "
        line += "Ex: `ae8803-non` for AE 8803 \"Nonlinear Control Systems\""
        line += "\nIf that is a valid course, it is also possible that this topic has not been added to my memory."
        line += "If it was, please use the `!add` command to add it to my memory. "
        line += "(ex: `!add ece1000 Intro to Electrical Engineering`)"
        self.append(line)

    def append_course_unknown(self, course : Course):
        """Append the "I have never heard of this course" message"""

        line = 'Sorry, I have never heard of \" {} \". '.format(course.raw_string, course.get_full_semester())
        line += "Please double check that it was typed correctly. "
        line += "If it was, please use the `!add` command to add it to my memory. "
        line += "(ex: `!add ece1000 Intro to Electrical Engineering`)"
        self.append(line)

    def append_join_message(self, context, followed_instructions : bool):
        """Append the "Welcome to the Server" message
        
        Args:
            context : Discord context, needed to mention channels
            followed_instructions : if the user followed the join instructions. Just changes the message slightly"""

        requests_channel = discord.utils.get(context.guild.text_channels, name="course-requests")

        line = ""

        if followed_instructions:
            line += "You've been added to the general channels! Feel free to look around and ask questions!"
            line += "\n\nIf you would like to be added to any courses this semester, "
        else:
            line += "You've also been added to the general channels! Feel free to look around and ask questions!"
            line += "\n\nIf you would like to be added to any additional courses,"

        line += f" head over to {requests_channel.mention}. There, type `!register` and then the courses you'd like to be added to."
        line += " For example `!register ae1000,ae1001` would register you for AE 1000 and AE 1001. "
        line += "Capitalization and spaces don't matter, just make sure you separate each course using a comma"
        line += "\n\nRob is the admin so if you need anything just type `@Rob` in your message and he'll get an alert."
        self.append(line)

    def append_added_to_memory(self, course : Course):
        """Append the "the course has been added to my memory" message"""

        self.append(course.get_course_and_title() + " has been added to my memory.")

    def append_add_misunderstood(self, arg : str):
        """Append the "that was not valid" message"""
        
        line = "I did not understand \"" + arg + "\". Please use the format \"deptCourse title\". Ex: \"ece1000 Into to Electrical Engineering\""
        self.append(line)