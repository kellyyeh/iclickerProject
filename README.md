# IclickerProject

Networking Components: 

Thanks to Python, Django and Django Channels, we were able to implement a web application with very ambitious features. We decided to use these tools because it allowed us to complete our goal without as much heavy lifting. Once we had configured the fundamental asynchronous connection of Django Channels for the server and multiple clients, we spent time working on the user interface, user experience, login functionality, database/model creation, and CSV uploading. In terms of synchronous connections, we were able to establish the primary HTTP connection between a user and the web application’s server. An HTTP request example is when a user makes an HTTP request, we create a new http scope with the user’s path, method, and headers. Then, our web app can send an http.request event with HTTP content. On the other end, a http.response event is generated back to the browser. Afterwards, the connection is permanently closed.
Django channels is our project’s integration layer which allows us to implement WebSockets built over ASGI. The channels application has capability to handle asynchronous connections and sockets, and our main website uses HTTP protocols with synchronous connections. When a server creates a new asynchronous connection, we want to disallow all clients from IP addresses that do not match UCSB’s private network IP address. When a professor creates a new lecture iClicker session, on the backend, a channel layer “group” is created on the live server. From there, every time a student/client logs in with the correct lecture id, they are added into the same group, called ‘lecture’. For added security, we only allow asynchronous client connections to the server when the lecture id parameter is correct and the IP address is permitted. This allows the professor to securely broadcast messages to everyone in the lecture (the students), which creates our fundamental iClicker functionality. The professor can choose to broadcast multiple questions while the asynchronous connection is kept alive, or, he/she can close the “lecture” session and kick out everyone else. We use Docker and Daphne together to locally host the server and the client simultaneously. Daphne handles the transitions between synchronous and asynchronous connections for us.
We use sessions to save important information pertaining to a currently logged in user, such as a session key, session user, session lecture id, and so forth. Sessions comes from Django’s SessionMiddleware feature. Each time an HTTP Request object is generated, the session dictionary is passed along with the request. This upholds the integrity of a single user’s experience past login and lets us pass data to new website views. For more permanent information, we connected our application to the sqlite3 database. 
