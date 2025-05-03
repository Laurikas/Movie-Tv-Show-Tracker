Coursework Report
Object-Oriented Programming – Python Application
Movie & TV Show Tracker



1.	Introduction

The goal of this project was to build a Python app using object-oriented programming (OOP). I decided to make a web app called the "Movie & TV Show Tracker" which helps users keep track of the movies, TV shows, and actors they like. The main idea was to use OOP concepts like encapsulation, abstraction, and inheritance while making something practical.
The app was built using Python, Flask, and SQLAlchemy. It lets users search, view, and manage a collection of movies and shows. I also connected it to the TMDB (The Movie Database) API so it can fetch real movie data. Everything was developed in a virtual environment, and I uploaded the finished code to GitHub.



2.	Problem Definition and Requirements

Not long ago, I wanted to make a list of all the movies and shows I had watched. I found it surprisingly hard to find a simple app that did exactly what I wanted. That’s why I decided to make my own version that’s straightforward and easy to use.
Functional features I added:
•	Add, update, and delete movies and TV shows
•	Show detailed info for each item
•	Actor pages that show what they've been in
•	A search and filter option
•	API integration for real movie data

Non-functional goals:
•	Good performance using SQLAlchemy
•	Clean and reusable code using OOP



3.	Design and Implementation

I tried to keep everything organized using OOP from the start. Each part of the app was written to do a specific task, and I kept things flexible for future updates.
Main classes I created:
•	Movie and TVShow for the different types of media
•	Actor for people connected to the media
•	MediaService to handle API calls and responses
•	I also thought about having a MediaItem base class to group shared features, but it wasn’t fully needed

I used Flask for the web side of the app since it works well with Python and is simple to use. For storing data, I picked SQLAlchemy, partly because we’re also studying databases this semester. Each class links to a table in SQLite, and I set up relationships so actors can be linked to multiple movies.
Jinja2 templates helped me display content like search results and detail pages. I styled everything with CSS to make the site easier to use. I used the TMDB API to pull real movie data, like posters and summaries, using the requests module.

4.	Development Process

I used Visual Studio Code for coding, a virtual environment to manage dependencies, and GitHub for version control. I also used GitHub Copilot to help with suggestions now and then.
The steps I followed:
1.	Thinking through the idea
2.	Choosing tools and tech
3.	Setting up basic Flask routes
4.	Writing classes using OOP
5.	Adding the TMDB API connection
6.	Making templates and adding design
7.	Testing everything and fixing bugs
8.	Uploading the project to GitHub with a README and .gitignore
9.	Results and Demonstration

The app now has these features:
•	Add or browse movies and shows with details
•	Actor pages with their roles
•	Search function by title
•	Real posters and info from the TMDB API
•	A simple, clean design

One part that didn’t go as planned was the "View Movies" page. I wanted it to look like the search results page, with posters, ratings, and links, but I ran into trouble passing API data into my own database. This part is still basic and shown in table form for now. Aswell as the Add Movie or Add Tv Show was useful at the start of development when I was designing the database to store these items, but later on as I added the external TMDB database this became useless, but I decided to keep it for show.



6.	Testing and Validation

I tested everything manually in the browser. I checked that all the routes worked, made sure the forms handled errors, and verified that missing or broken data didn’t crash the app. I also used some basic automated checks for the database and functions.



7.	Conclusion and Future Work

The app mostly met its goals. It works as a simple way to track movies and shows using object-oriented design. There are still things to improve, but overall, it was a great learning experience.
Future features I’d like to add:
•	User logins so people can have personal lists
•	A way to rate and review movies
•	Recommendations based on what users like
•	Hosting the app online so others can use it
This project helped me understand how to build something from scratch using both OOP and web development tools. It also gave me more confidence working with APIs, databases, and GitHub.