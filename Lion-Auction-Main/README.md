CMPSC 431W README  							           
Name: Stanley Wang


HEADS UP: <br />
THIS PROGRAM IS STILL A PROTOTYPE, CURRENTLY ONLY USER LOGIN FUNCTION WORKS

Context:
1. Current stage of the program is still in prototype phase, but most of the functionality
   has been implemented. Users are able to login to 3 types of account, and able to use a
   functioning auction system. This including able to browse product, buy and sell products,
   see user activity history, and some minor functionality such as a profile page.

2. Features:
   1. Index page: <br />
        On this page a drop-down table is displayed, this dropdown table
        is controlled by select() function in app.py, which based on the
        selection it would assign a value (empty, option_1, option_2, option_3),
        which the select() function will detect and will take you to
        the corresponding page.
   2. login page page: <br />
        On this page, 2 entry boxes are given where first box is for user
        to enter their username/login info, and the second box for their password. There
        are also two buttons which one will return you to the first page,
        and the other button "login" will ask you to confirm if you want to
        login (this is for testing purpose only). If you select no, no
        action will be taken, otherwise if you select yes, the user login information
        will be checked, and if it fails then user will be redirected to
        an error page shows login failed, where they can try again, or if
        successful they will be redirected to home page.
   3. register page: (not fully functioning) <br />
        On this page, user is able to register their own account and select the type of
        account they want to register, although the functionality is still not fully
        implemented, but hashing passwords are working fine.
   4. home page: <br />
        There are 4 different home pages, one for seller, one for bidder, one for vendor,
        and one for helpdesk. Each of these home pages have different functions due to
        the difference in account role. Seller and vendor would have the ability to sell
        and bid, while bidder can only bid, and helpdesk currently only have profile as
        their function. Seller and vendors can also see their balance.
   5. browsing: <br />
        On this page use is able to select the item they want to bid. All item that are
        listed are currently active, user can also select the category they want, or
        just straight up search for the product.
   6. bidding pages: <br />
        Users are able to bid on bidding pages, these pages not just contain the product
        information, users are also able to place price on these pages.
   7. profile page: <br />
        Every user have their unqiue profile page, depending on account information that
        shows up on profile page also varies. For example profile page of vendors account
        shows their company, while normal seller account shows their personal info.
   8. bid history: <br />
        bid history shows viewer's current active bids they participate in, and also
        past bids that viewer has been participated in.
   9. sale history: <br />
        sellers can also see their own sale history, items that are sold or items that are
        still being sold.
   10. Notifications: <br />
        this page is to check if an auction have ended. Bidder will recieve a notification
        if the auction has ended and they are the winner. Seller can also see those
        notification, but they are also able to see their sold product as who won, and how
        much they were paid.
   11. Sale management: <br />
        sellers are able to manage their own sales, by either changing the sale status to
        active or inactive, when they put an item as inactive, the item is removed from
        listing, and also clear all participent.
   12. Payment history: <br />
        Both bidder and seller can see the history payment they made for each auction they
        have participated and won. But seller can also see their income of the product
        that they have sold.


3. The files are organized where all the html files are within the templates
    folder, since these controls what were being shown on the webpage. There
    are also app.py, hashing.py, Users.csv, database.db, and README.md
    which are outside of the template folder, where app.py is the
    execution file, database,db contains all the database,
    README.md is just a readable file for reading, hashing.py is a stand alone
    program that I used to hash the passwords within the table, and Users.csv
    contains all the login required for this section.

    Update: now addition to these files, all the other csv files are also imported
    for implementation use, a new winner_table.py is added for creating the winner table

4. In order to run this project, first you have to have python installed,
    then you will need flask within pycharm. After these things are installed
    you need to open project and select this folder. When you run the code,
    you want to make sure you run the app.py file instead of the html file,
    which if you run the html file it would not work. After you run the
    app.py file there should be a clickable link that pops up in the console,
    click on that link and navigate to that website. On the first page, there
    will be a drop-down box asking you for a selection. If you don't select
    anything and run, nothing will happen. If you select "User login",
    it will take you to a page where you can login.


Reference:
1. Dropdown: TA office hour
2. Bootstrap: https://getbootstrap.com/docs/4.0/components/modal/
3. SQL: Chapter 2 slides
4. Schema: Chapter 3 slides
5. Hashing: https://www.geeksforgeeks.org/how-to-hash-passwords-in-python/
6. Citation for date implementation: https://stackoverflow.com/questions/65548490/how-to-get-current-date-time-in-python-flask
7. Citation for flask session: https://www.geeksforgeeks.org/how-to-use-flask-session-in-python-flask/
8. Citation for profile page styling: https://www.w3schools.com/howto/tryit.asp?filename=tryhow_css_split_screen
9. Citation for html image: https://www.w3schools.com/html/html_images.asp
10. Citation for split button: https://stackoverflow.com/questions/35575529/align-two-buttons-horizontal-to-each-other
11. Citation navigation bar: https://www.w3schools.com/howto/howto_css_dropdown_navbar.asp
