-- A single course
CREATE TABLE courses (
  dept TEXT NOT NULL, -- Dept code. Ex: AE, ECE, ME
  course TEXT NOT NULL, -- course code. Ex: 6122, 8803
  topic TEXT NOT NULL DEFAULT 0, -- topic (only relevant for special topics courses, 0 for other courses). Ex: NON (first 3 letters of Nonlinear)
  title TEXT NOT NULL, -- course name. Ex: Advanced Computer Programming
  special INTEGER DEFAULT 0, -- If this course is a special topics course. 0 (False) or 1 (True). Integer because boolean doesn't exist
  PRIMARY KEY (dept ASC, course ASC, topic ASC) -- dept, course, and topic are composite primary key and are all sorted ascending
);

-- A course in a specific semester.
--This directly connects to Discord's categories so we'll use the category ID as the key
CREATE TABLE registrar (
  category_id INTEGER PRIMARY KEY, -- The Discord Category (channel) ID
  year TEXT NOT NULL, -- Ex: 2021
  semester TEXT NOT NULL, -- Ex: Fall, Spring
  semester_sort TEXT NOT NULL, -- sorting order for the semester: 1-Spring, 2-Summer, 3-Fall, 
  dept TEXT NOT NULL, -- dept code. references courses table
  course TEXT NOT NULL, -- course code. references courses table
  topic TEXT NOT NULL DEFAULT 0, -- topic (only relevant for special topics courses, 0 for other courses). references courses table

  FOREIGN KEY(dept) REFERENCES courses(dept),
  FOREIGN KEY(course) REFERENCES courses(course),
  FOREIGN KEY(topic) REFERENCES courses(topic)
);

-- A user in a given course in a given semester.
-- The combination of user and category (ie course offering) should be unique
-- This directly connects Discord category permissions
CREATE TABLE schedule (
  id INTEGER PRIMARY KEY, -- since this list will likely get long, we'll just use an id to handle it
  user INTEGER NOT NULL, -- user's Discord ID
  username TEXT NOT NULL, -- user's Display name (for human readability)
  category_id INTEGER NOT NULL, -- Discord category id (represents a specific course offering)
  hidden INTEGER DEFAULT 0, -- if they were removed from the group (at their request) but didn't "drop" the course. SQLITE doesn't have true boolean, so using integers instead
  
  FOREIGN KEY (category_id) REFERENCES registrar(category_id)
);

-- Hold all of the pending requests (waiting for more people to join before creating the group)
CREATE TABLE requests (
  dept TEXT NOT NULL,
  course TEXT NOT NULL,
  topic TEXT NOT NULL,
  year TEXT NOT NULL, -- Ex: 2021
  semester TEXT NOT NULL, -- Ex: Fall, Spring
  user INTEGER NOT NULL, -- user's Discord ID
  username TEXT NOT NULL, -- user's Display name (for human readability)

  FOREIGN KEY(dept) REFERENCES courses(dept),
  FOREIGN KEY(course) REFERENCES courses(course),
  FOREIGN KEY(topic) REFERENCES courses(topic)
);