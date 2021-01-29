import discord, sqlite3, re
from discord.ext import commands
from enum import Enum
import logging
from dotenv import load_dotenv
import os

# load environment variables
load_dotenv('.env')

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='buzz-bot.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

logger.info("Buzz-Bot started")

# Config Variables
current_year = "2021"
current_year_short = "21"
current_semester = "Spring"
current_semester_short = "Sp"
current_semester_sort = "1-" + current_semester

# Global Database Variables
Courses_Columns = Enum('Courses_Columns', ['dept', 'course', 'topic', 'title', 'special'], start=0)
Registrar_Columns = Enum('Registrar_Columns', ['category', 'year', 'semester', 'semester_sort', 'dept', 'course', 'topic'], start=0)
Requests_Columns = Enum('Requests_Columns', ['dept', 'course', 'topic', 'year', 'semester', 'user'], start=0)
Schedule_Columns = Enum('Schedule_Columns', ['id', 'user', 'category', 'hidden'], start=0)

# Set up the sqlite database
conn = sqlite3.connect("GT.db")

# Set up the discord intents
intents = discord.Intents.default()
intents.members = True

# Create the discord bot with a given prefix and no default help command (A custom one is defined below)
bot = commands.Bot(command_prefix='!', help_command=None, intents=intents)


################################ Database Functions ################################

def db_get_course(dept, course, topic):
    """Query the database to see if the course is valid (ie "already known")

    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (integer): the topic

    Returns:
        row (list): return all the rows returned by the query
    """

    # Build query to get the course from the database
    sql = "SELECT * FROM courses WHERE dept='" + dept + "' AND course='" + course + "' AND topic='" + topic + "'"
    logger.debug("db_get_course query: \"" + sql + "\"")
    return conn.execute(sql).fetchall()

def db_is_course_special_topics(dept, course):
    """Query the database to see if the course is a special topics course

    Args:
        dept (string): the department the course is in
        course (string): the course code

    Returns:
        boolean: if the course is a special topics course
    """

    # Build query to get the course from the database
    sql = "SELECT * FROM courses WHERE dept='" + dept + "' AND course='" + course + "' AND special=1"
    logger.debug("db_is_course_special_topics query: \"" + sql + "\"")
    row = conn.execute(sql).fetchall()

    if row: # if there were any courses returned (there could be more than one)
        return True # then the course is a special topics course
    else: # the course is not a special topics course (or doesn't exist at all)
        return False

def db_get_course_available(dept, course, topic):
    """Query the database to see if the course is available (ie "already exists")
    
    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (string): the course topic (only relevant for special topics courses, 0 for other courses)

    Returns:
        bool: True if the course is available, False otherwise
    """

    # Build query to check if the course is in the registrar table
    sql = "SELECT * FROM registrar WHERE dept='" + dept + "' AND course='" + course + "' "
    sql += "AND topic='" + topic + "' AND year='" + current_year + "' AND semester='" + current_semester + "'"
    logger.debug("db_get_course_available query: \"" + sql + "\"")
    return conn.execute(sql).fetchall() # Return what the query returned

def db_get_course_requested(dept, course, topic):
    """Query the database to see if the course is in the requested list (already been requested)

    Args:
        \tdept (string): the department the course is in\n
        \tcourse (string): the course code\n
        \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n

    Returns:
        the row of returned query of if a course was requested
    """

    # Build query to check if the course is in the requests table
    sql = "SELECT * FROM requests WHERE dept='" + dept + "' AND course='" + course + "'"
    sql += " AND topic='" + topic + "' AND year='" + current_year + "' AND semester='" + current_semester + "'"
    logger.debug("db_get_course_requested query: \"" + sql + "\"")
    return conn.execute(sql).fetchall() # Return what the query returned

def db_join_course(user, username, category_id):
    """Add a user to a course in the current semester

    Makes the relevant changes in both Discord itself and the database

    Args:
        user (integer): the Discord user unique ID
        category (integer): the Discord category unique ID
    """

    # Build query to add the user to the schedule
    sql = "INSERT INTO schedule (user, username, category_id) VALUES('" + str(user) + "', '" + username + "', '" + str(category_id) + "')"
    logger.debug("db_join_course query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_create_course_registration(dept, course, topic, category_id):
    """Create a specific instance of a course
    
    Args:\n
        dept (str): the department the course is in\n
        course (str): the course code\n
        topic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n
        category_id (int): the Discord category ID
    """
    
    # Insert the course into the registrar table
    sql = "INSERT INTO registrar (category_id, year, semester, semester_sort, dept, course, topic) "
    sql += "VALUES('" + str(category_id) + "', '" + current_year + "', '" + current_semester + "', '" + current_semester_sort
    sql += "', '" + dept  + "', '" + course  + "', '" + topic + "')"
    logger.debug("db_create_course_registration query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_create_course(dept, course, topic, title):
    """Create a course
    
    Args:\n
        \tdept (string): the department the course is in\n
        \tcourse (string): the course code\n
        \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n
        \ttitle (integer): the name of the course
    """
    
    # Insert the course into the registrar table
    sql = "INSERT INTO courses (dept, course, topic, title, special) "
    sql += "VALUES('" + dept  + "', '" + course  + "', '" + topic + "', '" + title + "', "
    if topic != "0": # if the topic is not "0", then it is a special topics course
        sql += "'1')"
    else:
        sql += "'0')"
    logger.debug("db_create_course query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_request_course(dept, course, topic, user, username):
    """Create a course request
    
    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (string): 
        user (integer): Discord ID of the requesting user

    """
    
    # Insert the course into the requests table
    sql = "INSERT INTO requests (dept, course, topic, year, semester, user, username) "
    sql += " VALUES('" + dept  + "', '" + course  + "', '" + topic + "', '" + current_year + "', '" + current_semester + "', '" 
    sql += str(user) + "', '" + username + "')"
    logger.debug("db_request_course query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_clear_request(dept, course, topic, user):
    """Delete a course request
    
    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (string): the topic (only )
        user (integer): Discord ID of the requesting user

    """
    
    # Remove the request from the requests table
    sql = "DELETE FROM requests WHERE dept='" + dept + "' AND course='" + course + "'"
    sql += " AND topic='" + topic + "' AND year='" + current_year + "' AND semester='" + current_semester + "'"
    sql += " AND user='" + str(user) + "'"
    logger.debug("db_clear_request query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

################################## Bot Commands ##################################

# Help Message
@bot.command(name="help")
async def help(context):
    message = "Here a list of what I can do:"
    
    message += "\n\n__**register**__ - join a course or list of courses (separated by commas). Capitalization and spaces don't matter, just make sure you separate multiple courses using a comma"
    message += "\n> Ex: `!register ae1000,ae1001` would register you for AE 1000 and AE 1001."
    message += "\n\n> Note: If this course is a special topics course (ie, all sections are not taught together, usually covering different topics), then include a \"-\" and the first 3 letters of the course name. Ex: `!register ae8803-non` would add you to the \"Nonlinear\" section of AE 8803"
    
    message += "\n\n__**add**__ - add an unknown course (this is needed when you try to register for a course I've never seen before). The department code, course code, and the course title are needed, in that order."
    message += "\n> Ex: `!add ECE 1000 Intro to Electrical Engineering` would add the course ECE 1000 and call it \"Into to Electrical Engineering\""
    
    # message += "\n\n__**hide**__ - hide a given course or all courses from the sidebar."
    # message += "\n> Ex: `!hide ae1000.` would hide AE 1000 and `!hide all` would hide all courses"
    
    # message += "\n\n__**show**__ - show a given course (that you had hidden) or all your courses in the sidebar."
    # message += "\n> Ex: `!show ae1000.` would show AE 1000 and `!show all` would show all your courses"
    
    # message += "\n\n__**drop**__ - remove yourself entirely from a given course."
    # message += "\n> Ex: `!drop ae1000`. would completely remove you from AE 1000"

    message += "\n\n__**help**__ - show this message"

    message += "\n\nRob is the admin so if you need anything else you can mention him in a message (just type `@Rob` or `@Admin`) or send him a private message and he'll get an alert."

    await context.message.channel.send(message)


# Join command to get basic access to the server and instructions on how to add courses
@bot.command(name="join")
async def join(context):
    user = context.message.author # get the member who requested access
    await user.add_roles(discord.utils.get(user.guild.roles, name="Yellow Jackets")) # give the Yellow Jackets role (which grants basic server access)

    # Build message tell them how to register for courses
    message = "You've been added to the general channels! Feel free to look around and ask questions!"
    message += "\n\nIf you would like to be added to any courses this semester, head over to <#755950528646610945>. There, just type `!register` and then the courses you'd like to be added to."
    message += " For example `!register ae1000,ae1001` would register you for AE 1000 and AE 1001. Capitalization and spaces don't matter, just make sure you separate each course using a comma"
    message += "\n\nRob is the admin so if you need anything just type in your message `@Rob` and he'll get an alert."
    await context.message.channel.send(message)
    logger.info("join- " + user.display_name + "(" + str(user.id) + ")")


# Register for one or more courses
@bot.command(name="register")
async def register(context, *, arg):
    requestor = context.author
    courses = [x.strip() for x in arg.upper().split(',')] # split up each course
    
    # Create the message to send to the user
    message = "" 

    # iterate through all the courses
    for x in courses:
        temp = re.findall(r'\d+|\D+', x) # separate the dept course code for use in the database query
        dept = temp[0].strip()
        course = temp[1].strip()
        topic = "0" # default to 0

        if len(temp) > 2: # if the parsed course has more than 2 parts, then it includes a special topic
            topic = temp[2][1:].strip() # set the topic

        logger.info("register - Process course: " + dept + " " + course + "-" + topic)

        # main registration process

        course_row = db_get_course(dept, course, topic) # get the course information given the dept, course, and topic
        if course_row: # If the course was found (ie valid)
            logger.debug("register - course was valid: " + dept + " " + course + "-" + topic)
            scheduled = db_get_course_available(dept, course, topic) # get the registration information

            if scheduled: # if there were any course offerings (registrations)
                logger.debug("register - " + requestor.display_name + "(" + str(requestor.id) + ") joining " + dept + " " + course + "-" + topic)
                db_join_course(requestor.id, requestor.display_name, scheduled[0][Registrar_Columns.category.value]) # Add them to the course in the database
                category = context.guild.get_channel(scheduled[0][Registrar_Columns.category.value]) # Get the channel category object
                await category.set_permissions(requestor, view_channel=True, connect=True) # add them to the course in Discord (give them the correct permissions)
                
                # Build the message
                if message != "": # if the message is not currently blank
                    message += "\n" # add a new line for the additional message piece
                message += "You have been added to " + dept + " " + course
                if topic != "0":
                    message += "-" + topic
                logger.info("register - " + requestor.display_name + "(" + str(requestor.id) + ") joined " + dept + " " + course + "-" + topic)
            
            else: # If there was not a current course offering, check the requests
                logger.debug("register - course was not scheduled. checking requests")
                request = db_get_course_requested(dept, course, topic) # get any requests for the course
                
                if request: # if it has been requested
                    logger.debug("register - " + requestor.display_name + "(" + str(requestor.id) + ") had already requested " + dept + " " + course + "-" + topic)
                    previous_requestor_id = request[0][Requests_Columns.user.value]
                    previous_requestor = context.guild.get_member(previous_requestor_id) # get the full information of the previous requestor

                    if previous_requestor_id == requestor.id: # If the new requestor was also the previous requestor
                        logger.info("register - course was already requested, duplicate request by " + previous_requestor.display_name)
                        # then they've already requested it so just tell them they've successfully requested it (though we don't need to add it to the database again)
                        # Build the message
                        if message != "": # if the message is not currently blank
                            message += "\n" # add a new line for the additional message piece
                        message += "You have already requested " + dept + " " + course
                        if topic != "0":
                            message += "-" + topic
                        message += ". It will be created and you will be automatically added when there is another request for it."
                    
                    else: # If the user is not the previous requester, then they're the second requester
                        logger.debug("register - requestor was not previous requestor, creating course")
                        # Configure the permission overwrites
                        permission_overwrites = {
                            # set the default role to not see or connect to the channel (replicate the built-in "Private Category" switch)
                            context.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),

                            # Allow the users to view and connect to the channel
                            previous_requestor: discord.PermissionOverwrite(view_channel=True, connect=True),
                            requestor: discord.PermissionOverwrite(view_channel=True, connect=True)
                        }

                        # Create the category and associated channels on Discord with appropriate permissions
                        category_name = dept + " " + course + " (" + current_semester_short + "'" + current_year_short + ") - " + course_row[0][Courses_Columns.title.value]
                        category = await context.guild.create_category(category_name, overwrites=permission_overwrites) # Create the category
                        
                        channel_name_suffix = (dept + course + "-" + current_semester_short + current_year_short).lower()
                        await context.guild.create_text_channel("general-" + channel_name_suffix, category=category) # create the general text chat
                        await context.guild.create_text_channel("hw-" + channel_name_suffix, category=category) # create the hw text chat
                        await context.guild.create_voice_channel("voice-chat-" + channel_name_suffix, category=category) # create the voice chat

                        db_create_course_registration(dept, course, topic, category.id) # create the course in the registrar

                        db_join_course(requestor.id, requestor.display_name, category.id) # add current requestor to it
                        db_join_course(previous_requestor_id, previous_requestor.display_name, category.id) # add previous requestor to it
                        db_clear_request(dept, course, topic, previous_requestor_id) # clear the request now that it's been fulfilled
                        
                        # Build the message
                        if message != "": # if the message is not currently blank
                            message += "\n" # add a new line for the additional message piece
                        course_name_full = dept + " " + course
                        if topic != "0":
                            course_name_full += "-" + topic

                        message += f"{requestor.mention} - You have been added to " + course_name_full
                        message += f".\n{previous_requestor.mention} - You had previously requested " + course_name_full + " so you have been added to it automatically."
                        logger.info("register - course was already requested by " + previous_requestor.display_name + "(" + str(previous_requestor.id) + "). Created course and added " + requestor.display_name + "(" + str(requestor.id) + ")")
                
                else: # if the course has not been requested
                    logger.debug("register - course has not been requested. Creating request")
                    db_request_course(dept, course, topic, requestor.id, requestor.display_name)
                    
                    # Build the message
                    if message != "": # if the message is not currently blank
                        message += "\n" # add a new line for the additional message piece
                    message += "You are the first person to request " + dept + " " + course
                    if topic != "0":
                        message += "-" + topic
                    message += ". Once there is another request for it, I will create it and automatically add you to it."
                    logger.info("register - course had not been requested. Created request by " + requestor.display_name + "(" + str(requestor.id) + ")" + " for " + dept + " " + course + "-" + topic)

        else: # if the course was not valid
            logger.debug("register - course is not valid: " + x)
            if message != "": # if the message is not currently blank
                message += "\n" # add a new line for the additional message piece

            if db_is_course_special_topics(dept, course): # if that course is a special topics course, then they specified something incorrectly
                logger.info("register - course is special topics course but topic did not match: " + dept + " " + course + "-" + topic)
                message += "" + dept + " " + course + " is a special topics course but I didn't recognize the topic you specified."
                message += "\nThe topic is the first 3 letters of the course name and should be included after the course number with a dash. Ex: `ae8803-non` for AE 8803 \"Nonlinear Control Systems\""
            else:
                logger.info("register - course is entirely unknown (not special topics): " + dept + " " + course + "-" + topic)
                # Build the message
                message += "Sorry, I have never heard of \"" + dept + " " + course
                if topic != "0":
                    message += "-" + topic
                message += "\". Please double check that it was typed correctly. "
                message += "If it was, please use the `!add` command to add it to my memory. (ex: `!add ECE 1000 Intro to Electrical Engineering`)"

    await context.message.channel.send(message) # send the message to the channel!


# Create a new course
@bot.command(name="add")
async def add(context, *, arg):
    temp = re.findall(r'\d+|\D+', arg) # separate the dept and course code for use in the database query
    dept = temp[0].strip().upper() # make the dept all caps
    course = temp[1].strip()
    topic = "0"
    title = ""

    message = "" # the message to send back

    if temp[2].startswith('-'): # if the remainder of the string starts with a -, then it's a special topic
        topic = temp[2][1:4].upper() # extract the topic and make it all caps
        title = temp[2][5:].strip()
        message = dept + " " + course + "-" + topic + " \"" + title + "\" has been added to my memory."
    else:
        title = temp[2].strip()
        message = dept + " " + course + " \"" + title + "\" has been added to my memory."

    db_create_course(dept, course, topic, title)

    await context.message.channel.send(message) # send the message to the channel!


# Rebuild the database of courses and registrations
# @bot.command(name="rebuild")
# async def rebuild(context):
#     for category in context.message.guild.categories:
#         print(category.name + ": " + str(category.id))
        # temp = category.name.split(' ')
        # if len(temp) > 4:
        #     dept = temp[0]
        #     course = temp[1]
        #     temp2 = 
        #     semester = 
        #     title = ' '.join(temp[4:])
        #     print(title)

# Drop a course
# @bot.command(name="drop")
# async def drop(context, *, arg):

################################ Event Functions #################################

@bot.event
async def on_member_join(new_member):
    new_member_mention = new_member.mention
    welcome_channel = discord.utils.get(new_member.guild.text_channels, name="welcome") #bot.get_channel(797588095352176721) # get the welcome channel
    await welcome_channel.send(f"Hi {new_member.mention}! I'm the BuzzBot. I'm here to help get you situated. To complete the joining process please message back with \"!join\"")
   

# Get the Discord token from the environment and run the bot
bot.run(os.getenv('BUZZ_BOT_TOKEN'))
