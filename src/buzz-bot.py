import discord, sqlite3, math, logging, os
from discord.ext import commands
from enum import Enum
from dotenv import load_dotenv
from course import Course
from discord_message import DiscordMessage

# Config Variables
current_year = os.getenv('CURRENT_YEAR')
current_semester = os.getenv('CURRENT_SEMESTER')
logging_level = os.getenv('LOG_LEVEL')

# Set up logging
logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s: %(message)s', level=logging_level)

logger.info("Buzz-Bot started")

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
# All the functions to interact with the database

def db_get_course(course : Course):
    """Query the database to see if the course is valid (ie "already known")

    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (integer): the topic

    Returns:
        row (list): return all the rows returned by the query
    """

    # Build query to get the course from the database
    sql = "SELECT * FROM courses WHERE dept='" + course.dept + "' AND course='" + course.code + "' AND topic='" + course.topic + "'"
    logger.debug("db_get_course query: \"" + sql + "\"")
    return conn.execute(sql).fetchall()

def db_is_course_special_topics(course : Course):
    """Query the database to see if the course is a special topics course

    Args:
        dept (string): the department the course is in
        course (string): the course code

    Returns:
        boolean: if the course is a special topics course
    """

    # Build query to get the course from the database
    sql = "SELECT * FROM courses WHERE dept='" + course.dept + "' AND course='" + course.code + "' AND special=1"
    logger.debug("db_is_course_special_topics query: \"" + sql + "\"")
    row = conn.execute(sql).fetchall()

    if row: # if there were any courses returned (there could be more than one)
        return True # then the course is a special topics course
    else: # the course is not a special topics course (or doesn't exist at all)
        return False

def db_get_course_available(course : Course):
    """Query the database to see if the course is available (ie "already exists")
    
    Args:
    \tdept (string): the department the course is in
    \tcourse (string): the course code
    \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)
    \tyear (str): optional. defaults to current_year environment variable
    \tsemester (str): optional. defaults to current_semester environment variable

    Returns:
        bool: True if the course is available, False otherwise
    """

    # Build query to check if the course is in the registrar table
    sql = "SELECT * FROM registrar WHERE dept='" + course.dept + "' AND course='" + course.code + "' "
    sql += "AND topic='" + course.topic + "' AND year='" + course.semester.year + "' AND semester='" + course.semester.semester + "'"
    logger.debug("db_get_course_available query: \"" + sql + "\"")
    return conn.execute(sql).fetchall() # Return what the query returned

def db_get_course_requested(course : Course):
    """Query the database to see if the course is in the requested list (already been requested)

    Args:
        \tdept (string): the department the course is in\n
        \tcourse (string): the course code\n
        \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n
        \tyear (str): optional. defaults to current_year environment variable
        \tsemester (str): optional. defaults to current_semester environment variable

    Returns:
        the row of returned query of if a course was requested
    """

    # Build query to check if the course is in the requests table
    sql = "SELECT * FROM requests WHERE dept='" + course.dept + "' AND course='" + course.code + "'"
    sql += " AND topic='" + course.topic + "' AND year='" + course.semester.year + "' AND semester='" + course.semester.semester + "'"
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

def db_create_course_registration(course : Course, category_id):
    """Create a specific instance of a course
    
    Args:\n
    \tdept (str): the department the course is in\n
    \tcourse (str): the course code\n
    \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n
    \tcategory_id (int): the Discord category ID
    \tyear (str): optional. defaults to current_year environment variable
    \tsemester (str): optional. defaults to current_semester environment variable
    \tsemester_sort (str): optional. defaults to current_semester_sort environment variable
    """
    
    # Insert the course into the registrar table
    sql = "INSERT INTO registrar (category_id, year, semester, semester_sort, dept, course, topic) "
    sql += "VALUES('" + str(category_id) + "', '" + course.semester.year + "', '" + course.semester.semester + "', '" + course.semester.semester_sort
    sql += "', '" + course.dept  + "', '" + course.code  + "', '" + course.topic + "')"
    logger.debug("db_create_course_registration query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_create_course(course : Course):
    """Create a course
    
    Args:\n
        \tdept (string): the department the course is in\n
        \tcourse (string): the course code\n
        \ttopic (string): the course topic (only relevant for special topics courses, 0 for other courses)\n
        \ttitle (integer): the name of the course
    """
    
    # Insert the course into the registrar table
    sql = "INSERT INTO courses (dept, course, topic, title, special) "
    sql += "VALUES('" + course.dept  + "', '" + course.code  + "', '" + course.topic + "', '" + course.title + "', "
    if course.topic != "0": # if the topic is not "0", then it is a special topics course
        sql += "'1')"
    else:
        sql += "'0')"
    logger.debug("db_create_course query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_request_course(course : Course, user, username):
    """Create a course request
    
    Args:
        dept (string): the department the course is in
        course (string): the course code
        topic (string): 
        user (integer): Discord ID of the requesting user
        year (str): optional. defaults to current_year environment variable
        semester (str): optional. defaults to current_semester environment variable
    """
    
    # Insert the course into the requests table
    sql = "INSERT INTO requests (dept, course, topic, year, semester, user, username) "
    sql += " VALUES('" + course.dept  + "', '" + course.code  + "', '" + course.topic + "', '"
    sql += course.semester.year + "', '" + course.semester.semester + "', '" 
    sql += str(user) + "', '" + username + "')"
    logger.debug("db_request_course query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

def db_clear_request(course : Course, user):
    """Delete a course request
    
    Args:
    \tdept (string): the department the course is in
    \tcourse (string): the course code
    \ttopic (string): the topic (only )
    \tuser (integer): Discord ID of the requesting user
    \tyear (str): optional. defaults to current_year environment variable
    \tsemester (str): optional. defaults to current_semester environment variable
    """
    
    # Remove the request from the requests table
    sql = "DELETE FROM requests WHERE dept='" + course.dept + "' AND course='" + course.code + "'"
    sql += " AND topic='" + course.topic + "' AND year='" + course.semester.year + "' AND semester='" + course.semester.semester + "'"
    sql += " AND user='" + str(user) + "'"
    logger.debug("db_clear_request query: \"" + sql + "\"")
    conn.execute(sql) # Execute the query
    conn.commit() # Commit the change

############################### Helper Functions ###############################
# Some functions to help with discord

# Get the total number of channels in the server
def get_total_channels(context):
    return len(context.guild.text_channels) + len(context.guild.text_channels)

# Get the max number of courses that could be created
def get_max_courses_remaining(context):
    total_channels = get_total_channels(context)
    return math.floor((500-total_channels) / 4)

# Check the server limits and return a printable string
def check_limits(context):
    total_channels = get_total_channels(context)
    base_message = "Total channels currently: " + str(total_channels) + "\nMax courses remaining: " + str(get_max_courses_remaining(context))
    if total_channels > 450:
        logger.warning(base_message + "\nTotal channels approaching max.")
    else:
        logger.info(base_message)
    return base_message

################################## Bot Commands ##################################
# All the commands the bot will respond to

# Help Message
@bot.command(name="help")
async def help(context):
    message = "Here a list of what I can do:"
    
    message += "\n\n__**register**__ - join a course or list of courses (separated by commas). Capitalization and spaces don't matter, just make sure you separate multiple courses using a comma"
    message += "\n> Ex: `!register ae1000,ae1001` would register you for AE 1000 and AE 1001."
    message += "\n\n> Note: If this course is a special topics course (ie, all sections are not taught together, usually covering different topics), then include a \"-\" and the first 3 letters of the course name. Ex: `!register ae8803-non` would add you to the \"Nonlinear\" section of AE 8803"
    message += "\n\n> Note2: If you want to register for a course in a semester other than " + current_semester + " " + current_year + " (the current semester) then just add the semester and year to the end of any course. Ex: `!register ae1000-sp22,ae1001,ae8803-non-f22` would register you for AE 1000 in Spring 2022, AE 1001 in the current semester, and AE 8803 Nonlinear in Fall 2022."
    
    message += "\n\n__**add**__ - add an unknown course (this is needed when you try to register for a course I've never seen before). The department code, course code, and the course title are needed, in that order."
    message += "\n> Ex: `!add ece1000 Intro to Electrical Engineering` would add the course ECE 1000 and call it \"Into to Electrical Engineering\""
    
    # message += "\n\n__**hide**__ - hide a given course or all courses from the sidebar."
    # message += "\n> Ex: `!hide ae1000.` would hide AE 1000 and `!hide all` would hide all courses"
    
    # message += "\n\n__**show**__ - show a given course (that you had hidden) or all your courses in the sidebar."
    # message += "\n> Ex: `!show ae1000.` would show AE 1000 and `!show all` would show all your courses"
    
    # message += "\n\n__**drop**__ - remove yourself entirely from a given course."
    # message += "\n> Ex: `!drop ae1000`. would completely remove you from AE 1000 and you would need to join it again using !register"

    message += "\n\n__**help**__ - show this message"

    message += "\n\nRob is the admin so if you need anything else you can mention him in a message (just type `@Rob` or `@Admin`) or send him a private message and he'll get an alert."

    await context.message.channel.send(message)


# Join command to get basic access to the server and instructions on how to add courses
@bot.command(name="join")
async def join(context):
    user = context.message.author # get the member who requested access
    await user.add_roles(discord.utils.get(user.guild.roles, name="Yellow Jackets")) # give the Yellow Jackets role (which grants basic server access)

    message = DiscordMessage()
    message.append_join_message(context, True)

    await context.message.channel.send(message.message)
    logger.info("join- " + user.display_name + "(" + str(user.id) + ")")


# Register for one or more courses
@bot.command(name="register")
async def register(context, *, arg):
    requestor = context.author
    courses_raw = [x.strip() for x in arg.upper().split(',')] # split up each course request
    
    # Create the message to send to the user
    message = DiscordMessage()

    # iterate through all the courses they requested
    for x in courses_raw:
        potential_course = Course(x, current_year, current_semester)
        logger.info("register - Processing course: " + potential_course.raw_string)

        # check if the course is valid by checking the database
        course_row = db_get_course(potential_course)

        # If "course_row" is populated from the database call, then the course was found in the database (ie it is valid)
        if course_row:
            logger.debug("register - course was valid: " + str(potential_course))
            
            # Set the title of the course, returned from the database call
            potential_course.set_title(course_row[0][Courses_Columns.title.value])
            
            # get the registration information from the database
            scheduled = db_get_course_available(potential_course)

            # if "scheduled" is populated from the database call, then there are matching course offerings (registrations)
            if scheduled:
                logger.debug("register - " + requestor.display_name + "(" + str(requestor.id) + ") joining " + str(potential_course))

                # Add them to the course in the database
                db_join_course(requestor.id, requestor.display_name, scheduled[0][Registrar_Columns.category.value])

                # Get the Discord channel category object and add them to the course (give them the correct Discord permissions)
                category = context.guild.get_channel(scheduled[0][Registrar_Columns.category.value])
                await category.set_permissions(requestor, view_channel=True, connect=True)
                logger.info("register - " + requestor.display_name + "(" + str(requestor.id) + ") joined " + potential_course.get_full_name_and_semester())

                # Add a new line to the message to the user
                message.append_course_added(potential_course)
                
            # If there was not a current course offering, check the requests
            else:
                logger.debug("register - course was not scheduled. checking requests")
                
                # get any requests for the course
                request = db_get_course_requested(potential_course)
                
                # If "request" is populated from the database call, then it has been requested and we can add them to it
                if request:
                    logger.debug("register - " + requestor.display_name + "(" + str(requestor.id) + ") had already requested " + potential_course.get_full_name_and_semester())
                    
                    # get the full information of the previous requestor from the database call and then the Discord member object
                    previous_requestor_id = request[0][Requests_Columns.user.value]
                    previous_requestor = context.guild.get_member(previous_requestor_id) # TODO: Need to put a check here for if the previous requestor is no longer a member

                    # If the new requestor was also the previous requestor
                    if previous_requestor_id == requestor.id:
                        logger.info("register - course was already requested, duplicate request by " + previous_requestor.display_name)
                        
                        # they've already requested it so just tell them they had already requested it in a new line in the message to the user
                        message.append_course_already_requested(potential_course)
                    
                    # If the user is not the previous requester, then they're the second requester and the course should be created
                    else:
                        logger.debug("register - requestor was not previous requestor, creating course")

                        # If we cannot create any more courses, then we've got a problem. Continue in the loop and process the next course
                        if get_max_courses_remaining(context) < 1:
                            message.append("If you're reading this then unfortunately we've hit the course limit for this server and we've created courses faster than @Rob can make room for")
                            continue
                        
                        # Configure the permission overwrites
                        permission_overwrites = {
                            # set the default role to not see or connect to the channel (replicate the built-in "Private Category" switch)
                            context.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),

                            # Allow the requesting users to view and connect to the channel
                            previous_requestor: discord.PermissionOverwrite(view_channel=True, connect=True),
                            requestor: discord.PermissionOverwrite(view_channel=True, connect=True)
                        }

                        # Create the category and associated channels on Discord with appropriate permissions
                        category = await context.guild.create_category(potential_course.get_category_name(), overwrites=permission_overwrites) # Create the category
                        
                        channel_name_suffix = potential_course.get_channel_postfix_name().lower() # set the suffix to be used in each channel
                        await context.guild.create_text_channel("general-" + channel_name_suffix, category=category) # create the general text chat
                        await context.guild.create_text_channel("hw-" + channel_name_suffix, category=category) # create the hw text chat
                        await context.guild.create_voice_channel("voice-chat-" + channel_name_suffix, category=category) # create the voice chat

                        # Check the server limits and log them.
                        check_limits(context)

                        # Do all the associated database calls
                        db_create_course_registration(potential_course, category.id) # create the course in the registrar
                        db_join_course(requestor.id, requestor.display_name, category.id) # add current requestor to it
                        db_join_course(previous_requestor_id, previous_requestor.display_name, category.id) # add previous requestor to it
                        db_clear_request(potential_course, previous_requestor_id) # clear the request now that it's been fulfilled
                        

                        # Append to the message to the user
                        message.append_course_added(potential_course, f"{requestor.mention} - ")
                        message.append_course_previously_requested_added(potential_course, f"{previous_requestor.mention} - ")
                        
                        logger.info("register - course was already requested by " + previous_requestor.display_name + "(" + str(previous_requestor.id) + "). Created course and added " + requestor.display_name + "(" + str(requestor.id) + ")")
                
                else: # if the course has not been requested
                    logger.debug("register - course has not been requested. Creating request")
                    db_request_course(potential_course, requestor.id, requestor.display_name)
                    logger.info("register - course had not been requested. Created request by " + requestor.display_name + "(" + str(requestor.id) + ")" + " for " + potential_course.get_full_name())
                    
                    # Append to the message to the user
                    message.append_course_requested(potential_course)

        else: # if the course was not valid
            logger.debug("register - course is not valid: " + x)

            if db_is_course_special_topics(potential_course): # if that course is a special topics course, then they specified something incorrectly
                logger.info("register - course is special topics course but topic did not match a known one: " + potential_course.get_full_name())
                
                # Append to the message to the user
                message.append_course_unknown_topic(potential_course)

            else:
                logger.info("register - course is entirely unknown (not special topics): " + potential_course.get_full_name())
                # Append to the message to the user
                message.append_course_unknown(potential_course)
    
    message.append("--------------------") # Append a dashed line to separate each course


    # If they tried to register in the welcome channel before "joining", just give them access because they clearly know more or less what's going on
    if discord.utils.find(lambda r: r.name == 'Yellow Jackets', context.message.guild.roles) not in context.message.author.roles:
        await context.message.author.add_roles(discord.utils.get(context.guild.roles, name="Yellow Jackets")) # give the Yellow Jackets role (which grants basic server access)
        logger.info("automatically added after failling to follow join instructions- " + context.message.author.display_name + "(" + str(context.message.author.id) + ")")
        message.append_join_message(context, False) # Provide the context and indicate that the initial instructions were not followed (just changes the message slightly)

    await context.message.channel.send(message.message) # send the message to the channel!


# Create a new course
@bot.command(name="add")
async def add(context, *, arg):
    # split the command arguments using a space
    arg_components = arg.split(' ')

    # create a course object based on the name
    new_course = Course(arg_components[0])
    
    # Create the message to send to the user
    message = DiscordMessage()

    # if the new course is not possible, they likely didn't follow the format.
    if not new_course.is_possible:
        message.append_add_misunderstood(arg)
        logger.info("add - course not possible? : " + arg)

    else:
        logger.info("add - course created in database: " + new_course.get_full_name())
        # Join the remaining arguments into a single string and set it as the course title
        new_course.set_title(' '.join(arg_components[1:]))

        # create the course in the database
        db_create_course(new_course)

        # the message to send back to the requestor
        message.append_added_to_memory(new_course)

    await context.message.channel.send(message.message) # send the message to the channel!

# Check the server limits
@bot.command(name="checklimits")
async def checklimits(context):
    await context.message.channel.send(check_limits(context)) # send the message to the channel!
    

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
# These are functions that are automatically triggereg based on specific events

# Triggers whenever a member joins the server
@bot.event
async def on_member_join(new_member):
    welcome_channel = discord.utils.get(new_member.guild.text_channels, name="welcome")
    await welcome_channel.send(f"Hi {new_member.mention}! I'm the BuzzBot. I'm here to help get you situated. To complete the joining process please message back with \"!join\"")

# Watch all messages so as to only actually process the commands above in certain channels or if they're from an admin
@bot.event
async def on_message(message):
    if message.channel.name == 'course-requests' or message.channel.name == 'welcome' or message.channel.name == 'bot-testing' or discord.utils.find(lambda r: r.name == 'Admin', message.guild.roles) in message.author.roles:
        await bot.process_commands(message)

# Get the Discord token from the environment and run the bot
bot.run(os.getenv('BUZZ_BOT_TOKEN'))