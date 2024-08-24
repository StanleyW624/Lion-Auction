from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from datetime import datetime
import sqlite3 as sql
import bcrypt
import random


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

host = 'http://127.0.0.1:5000/'

#index page
@app.route('/')
def index():
    return render_template('index.html')

#1 is for seller, 2 for vendor, 3 for helpdesk, 0 for bidder
#select homepage base on account
@app.route('/find_home_page', methods=['POST','GET'])
def homepage():
    if not session.get("name"):
        return redirect('/name')

    if session.get("user_role") == 3:
        position = get_position_help_desk(session.get("name"))
        return render_template('help_desk_page.html', position=position)

    if session.get("user_role") == 2:
        balance = get_seller_balance(session.get("name"))
        return render_template('vendor_page.html', balance=balance)

    if session.get("user_role") == 1:
        balance = get_seller_balance(session.get("name"))
        return render_template('seller_page.html', balance=balance)

    if session.get("user_role") == 0:
        return render_template('bidder_page.html')



#browsing products
@app.route('/browsing', methods=['POST','GET'])
def browse():
    if not session.get("name"):
        return redirect('/name')
    result = parent_cat()
    condition = "All"
    subcondition = request.form.get("selected_cat")

    #show all selection to begin with
    #if result2 is none with click on go button for sub category, nothing should happen
    if result:
        show_0=ongoing_auc()
        return render_template('browsing.html', show_0=show_0, result=result, condition=condition, subcondition=subcondition)
    return render_template('browsing.html', result=result, condition=condition, subcondition=subcondition)

#this function is dedicated for user when the place a bid, such that bid page would update
@app.route('/bid_action', methods=['POST','GET'])
def bapage():
    if not session.get("name"):
        return redirect('/name')

    valid_auction = exist_payment(session.get("name"))

    if not valid_auction:
        return render_template('placebid_fail.html')

    id = request.form.get("sprice")
    bid_price = int(request.form['bidbox'])
    information = selected_product(id)
    listingemail = information[0][0]
    listingid = information[0][1]
    listing_price = information[0][7]
    listing_cap = information[0][8] #check to see if bidders are at max cap
    liststatus = information[0][9]

    if listingemail == session.get("name"):
        return render_template('placebid_fail.html')

    current_bids = showbids(listingid)

    amount_bidders = len(current_bids)

    if current_bids:
        current_highest = current_bids[0][2]
        highest_bidder_name = current_bids[0][1]

        for i in range(len(current_bids)):
            if (current_bids[i][2] > current_highest):
                current_highest = current_bids[i][2]
                highest_bidder_name = current_bids[i][1]
    else:
        current_highest = 0
        highest_bidder_name = None

    if listing_cap == amount_bidders:
        liststatus = 2
        updatestatus(listingemail,listingid,liststatus)
        update_winner(listingid,listingemail,highest_bidder_name,information[0][3],information[0][4],information[0][5],information[0][6],current_highest, "NOT PAID")
        return render_template('sold_out_page.html')
        #update status
        #return auction_closed

    if liststatus != 1:
        if liststatus == 0:
            return render_template('auction_closed.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)
        if liststatus == 2:
            return render_template('sold_auction.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)


    if highest_bidder_name == session.get("name"):
        return render_template("placebid_fail.html")

    if bid_price: #check if user want to bid
        lowest_price = int(listing_price.strip("$"))
        highest_bid = current_highest

        all_bid_id = get_bid_id()

        bid_id = random.randint(1,999999999)

        k=0
        while k in range(len(all_bid_id)):
            if all_bid_id[k][0] == bid_id:
                bid_id = random.randint(1, 999999999)
                k=0
            else:
                k+=1


        if (bid_price < lowest_price):
            return render_template("placebid_fail.html")
            #please enter a new price

        if (bid_price - highest_bid) < 1:
            #please enter a new price
            return render_template("placebid_fail.html")
        else:
            update_bids(bid_id, listingemail, listingid, session.get("name"), bid_price)
            current_bids = showbids(listingid)
            #update bid table using bid_id
            return render_template('auction_page.html', listingid=listingid, information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)

    return render_template('auction_page.html', listingid=listingid, information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)

#this was redundant, but it still functions as presenting auction page when first seen
@app.route('/auction_page', methods=['POST','GET'])
def apage():
    if not session.get("name"):
        return redirect('/name')
    id = request.form.get("bid_p")
    information = selected_product(id)
    listingemail = information[0][0]
    listingid = information[0][1]
    listing_price = information[0][7]
    listing_cap = information[0][8] #check to see if bidders are at max cap
    liststatus = information[0][9]

    current_bids = showbids(listingid)

    amount_bidders = len(current_bids)

    if current_bids:
        current_highest = current_bids[0][2]
        highest_bidder_name = current_bids[0][1]

        for i in range(len(current_bids)):
            if (current_bids[i][2] > current_highest):
                current_highest = current_bids[i][2]
                highest_bidder_name = current_bids[i][1]
    else:
        current_highest = 0
        highest_bidder_name = None



    try:
        bid_price = int(request.form['bidbox'])
    except:
        bid_price = None


    if listing_cap == amount_bidders:
        liststatus = 2
        updatestatus(listingemail,listingid,liststatus)
        update_winner(listingid,listingemail,highest_bidder_name,information[0][3],information[0][4],information[0][5],information[0][6],current_highest, "NOT PAID")
        return render_template('sold_out_page.html')
        #update status
        #return auction_closed

    if liststatus != 1:
        if liststatus == 0:
            return render_template('auction_closed.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)
        if liststatus == 2:
            return render_template('sold_auction.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)


    if highest_bidder_name == session.get("name"):
        return render_template("placebid_fail.html")

    if bid_price: #check if user want to bid
        lowest_price = int(listing_price.strip("$"))
        highest_bid = current_highest

        all_bid_id = get_bid_id()

        bid_id = random.randint(1,999999999)

        k=0
        while k in range(len(all_bid_id)):
            if all_bid_id[k][0] == bid_id:
                bid_id = random.randint(1, 999999999)
                k=0
            else:
                k+=1


        if (bid_price < lowest_price):
            return render_template("placebid_fail.html")
            #please enter a new price

        if (bid_price - highest_bid) < 1:
            #please enter a new price
            return render_template("placebid_fail.html")
        else:
            update_bids(bid_id, listingemail, listingid, session.get("name"), bid_price)
            #update bid table using bid_id
            return render_template('auction_page.html', listingid=listingid, information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)

    return render_template('auction_page.html', listingid=listingid, information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)






    #get value of the highest bid (use a for loop to find the highest price)
    #list all the bidder, and also check if bid is maxed out after a bid is placed,
    # if it is update the bid status
    #every bid have to be at least 1 dollar higher



#although this wasn't used, but this was suppose to be a page for auction that was inactive
@app.route('/closed_page', methods=['POST','GET'])
def cpage():
    if not session.get("name"):
        return redirect('/name')

    id = request.form.get("close_p")
    information = selected_product(id)

    listingid = information[0][1]

    current_bids = showbids(listingid)

    current_highest = current_bids[0][2]
    highest_bidder_name = current_bids[0][1]

    for i in range(len(current_bids)):
        if (current_bids[i][2] > current_highest):
            current_highest = current_bids[i][2]
            highest_bidder_name = current_bids[i][1]

    return render_template('auction_closed.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)

#this is for auction that have reached it's max capacity
@app.route('/ended_page', methods=['POST','GET'])
def epage():
    if not session.get("name"):
        return redirect('/name')

    id = request.form.get("end_p")
    information = selected_product(id)

    listingid = information[0][1]

    current_bids = showbids(listingid)

    current_highest = current_bids[0][2]
    highest_bidder_name = current_bids[0][1]

    for i in range(len(current_bids)):
        if (current_bids[i][2] > current_highest):
            current_highest = current_bids[i][2]
            highest_bidder_name = current_bids[i][1]

    return render_template('sold_auction.html', information=information, current_bids=current_bids, current_highest=current_highest, highest_bidder_name=highest_bidder_name)

#search bar for browsing page
@app.route('/searchbar', methods=['POST','GET'])
def sbar():
    if not session.get("name"):
        return redirect('/name')
    result = parent_cat()
    condition = "All"
    subcondition = "None"

    search = request.form['searchbox']

    if result:
        show_0 = s_ongoing_auc(search)
        return render_template('browsing.html', search=search, show_0=show_0, result=result, condition=condition, subcondition=subcondition)
    return render_template('browsing.html', search=search, result=result, condition=condition, subcondition=subcondition)


#main and sub category is controlled here
@app.route('/maincategory', methods=['POST','GET'])
def mcat():
    if not session.get("name"):
        return redirect('/name')
    # change both subcategory drop down and display all the related bits
    #search all item from this category
    result = parent_cat()

    condition = request.form.get("selected_par")
    subcondition = request.form.get("selected_cat")

    if result:
        if condition == "All":
            subcondition = "None"
            show_0 = ongoing_auc()
            #implement where if all is selected then everything shows
            return render_template('browsing.html', result=result, show_0=show_0, condition=condition, subcondition=subcondition)
        if condition == None:
            return render_template('browsing.html', result=result, condition=condition, subcondition=subcondition)
        else:
            if subcondition == "None":
                show_0 = main_product_OG(condition)
                result2 = cat_name(condition) #to update sub drop down table
                return render_template('browsing.html', result=result, show_0=show_0, result2=result2, condition=condition, subcondition=subcondition)
            else:
                new_result = check_valid(condition, subcondition)
                if new_result:
                    show_0 = sub_product_OG(subcondition)
                    result2 = cat_name(condition)
                    return render_template('browsing.html', result=result, show_0=show_0, result2=result2, condition=condition, subcondition=subcondition)
                else:
                    subcondition = "None"
                    show_0 = main_product_OG(condition)
                    result2 = cat_name(condition)
                    return render_template('browsing.html', result=result, show_0=show_0, result2=result2, condition=condition, subcondition=subcondition)
    return render_template('browsing.html', result=result, condition=condition, subcondition=subcondition)


# make sure when setting prices, check if the value is integer!!!

#this displays all the payment method a user have
@app.route('/bidderpayment', methods=['POST','GET'])
def bpay():
    if not session.get("name"):
        return redirect('/name')

    cards=find_credit(session.get("name"))
    return render_template('bidderpayment.html', cards=cards)

#user can remove a payment method
@app.route('/remove_card', methods=['POST','GET'])
def cremove():
    if not session.get("name"):
        return redirect('/name')

    card_remove = request.form.get("dcnum")
    remove_card(card_remove)

    cards = find_credit(session.get("name"))
    return render_template('bidderpayment.html', cards=cards)

#user can add a payment method
@app.route('/new_card', methods=['POST','GET'])
def ncard():
    if not session.get("name"):
        return redirect('/name')

    card_num = request.form.get("cnum")
    card_type = request.form.get("ctype")
    card_month = request.form.get("exp_month")
    card_year = request.form.get("exp_yr")
    card_code = request.form.get("scode")

    invalid = check_credit(card_num)

    if invalid:
        return render_template('add_card_fail.html')

    if card_num:
        if card_type:
            if card_month:
                if card_year:
                    if card_code:
                        cards = add_credit(card_num,card_type,card_month,card_year,card_code,session.get("name"))
                        return render_template('bidderpayment.html', cards=cards)

    return render_template('add_card_fail.html')

#vendor profile page
@app.route('/vendorinfo', methods=['POST','GET'])
def vinfo():
    if not session.get("name"):
        return redirect('/name')

    vendor_info = local_vendor_info(session.get("name"))

    cname = vendor_info[0][1]
    email = session.get("name")
    bphone = vendor_info[0][3]

    address_id = vendor_info[0][2]

    address_info = get_address_info(address_id)
    zipcode = address_info[0][1]
    street_num = address_info[0][2]
    street_name = address_info[0][3]

    zipcode_info = get_zipcode_info(zipcode)
    city = zipcode_info[0][1]
    state = zipcode_info[0][2]

    return render_template('vendor_info.html', state=state, city=city, street_name=street_name, street_num=street_num, cname=cname, email=email, bphone=bphone, zipcode=zipcode)

#staff profile page
@app.route('/staffinfo', methods=['POST','GET'])
def hdinfo():
    if not session.get("name"):
        return redirect('/name')

    info = get_bidder_info(session.get("name"))

    email = session.get("name")
    first = info[0][1]
    last = info[0][2]
    gender = info[0][3]
    age = info[0][4]

    return render_template('help_desk_info.html', age=age,email=email,first=first,last=last,gender=gender)

#seller profile page
@app.route('/sellerinfo', methods=['POST','GET'])
def sinfo():
    if not session.get("name"):
        return redirect('/name')

    info = get_bidder_info(session.get("name"))

    email = session.get("name")
    first = info[0][1]
    last = info[0][2]
    gender = info[0][3]
    age = info[0][4]
    major = info[0][6]

    address_id = info[0][5]

    address_info = get_address_info(address_id)
    zipcode = address_info[0][1]
    street_num = address_info[0][2]
    street_name = address_info[0][3]

    zipcode_info = get_zipcode_info(zipcode)
    city = zipcode_info[0][1]
    state = zipcode_info[0][2]

    bank_info = get_bank_info(session.get("name"))
    bankr = bank_info[0][1]
    bankan = bank_info[0][2]

    return render_template('bidder_info.html', bankan=bankan, bankr=bankr, state=state, city=city, street_name=street_name, street_num=street_num, major=major, email=email, first=first, last=last, gender=gender, age=age, zipcode=zipcode)

#bidder profile page
@app.route('/bidderinfo', methods=['POST','GET'])
def binfo():
    if not session.get("name"):
        return redirect('/name')

    info = get_bidder_info(session.get("name"))

    email = session.get("name")
    first = info[0][1]
    last = info[0][2]
    gender = info[0][3]
    age = info[0][4]
    major = info[0][6]

    address_id = info[0][5]

    address_info = get_address_info(address_id)
    zipcode = address_info[0][1]
    street_num = address_info[0][2]
    street_name = address_info[0][3]

    zipcode_info = get_zipcode_info(zipcode)
    city = zipcode_info[0][1]
    state = zipcode_info[0][2]

    return render_template('bidder_info.html', state=state, city=city, street_name=street_name, street_num=street_num, major=major, email=email, first=first, last=last, gender=gender, age=age, zipcode=zipcode)

#show history on bids the user have participated in
@app.route('/participated_bids', methods=['POST','GET'])
def pbids():
    if not session.get("name"):
        return redirect('/name')

    show_0=user_ongoing_auc(session.get("name"))
    show_2=user_sold_auc(session.get("name"))
    return render_template('participation_bid.html', show_0=show_0, show_2=show_2)

#notify user if they win a bid
@app.route('/bid_notification', methods=['POST','GET'])
def bid_notification():
    if not session.get("name"):
        return redirect('/name')

    status = "PAID"
    status2 = "NOT PAID"
    wins_paid = get_winner(session.get("name"),status)
    wins_not_paid = get_winner(session.get("name"),status2)

    return render_template('bid_notification.html', wins_paid=wins_paid, wins_not_paid=wins_not_paid)

#pays the winning product
@app.route('/paying', methods=['POST','GET'])
def paying():
    if not session.get("name"):
        return redirect('/name')

    dates = datetime.now()

    cards = find_credit(session.get("name"))

    if cards:
        new_status = "PAID"
        listing = request.form.get("listing")  # getting listing id

        sells = get_price_winner(session.get("name"), listing)

        seller = sells[0][0]  # seller email
        price = sells[0][1]  # payment

        update_winner_paid_status(session.get("name"), listing, seller, new_status)



        seller_balance = get_seller_balance(seller)

        new_balance = seller_balance[0][0] + price

        update_seller_balance(seller, new_balance)



        all_transaction_id = get_transaction_id()

        transaction_id = random.randint(1, 999999999)

        k = 0
        while k in range(len(all_transaction_id)):
            if all_transaction_id[k][0] == transaction_id:
                transaction_id = random.randint(1, 999999999)
                k = 0
            else:
                k+=1

        update_transaction_history(transaction_id, seller, listing, session.get("name"), dates.strftime("%d/%m/%y"), price)

        # this is to refresh page
        status = "PAID"
        status2 = "NOT PAID"
        wins_paid = get_winner(session.get("name"), status)
        wins_not_paid = get_winner(session.get("name"), status2)

        return render_template('bid_notification.html', wins_paid=wins_paid, wins_not_paid=wins_not_paid)
    else:
        return render_template('bidderpayment.html', cards=cards)

    #use listing id to get highest price
    #use listing id to change

    #add price to seller balance

    #check to see if there is payment method!!!!!!


#this shows the user's payment history
@app.route('/transaction_history', methods=['POST','GET'])
def t_his():
    if not session.get("name"):
        return redirect('/name')

    user_transaction = get_transaction_info_bidder(session.get("name"))
    return render_template('transaction_history.html', user_transaction=user_transaction)

#for seller to create a new sale entry
@app.route('/new_sale', methods=['POST','GET'])
def new_sale():
    if not session.get("name"):
        return redirect('/name')

    result = parent_cat()
    result2 = sub_cat_name()

    condition = "selection_0"
    subcondition = "selection_1"
    return render_template('new_sale.html', result=result, result2=result2, condition=condition, subcondition=subcondition)

#for putting up item on the browsing page
@app.route('/selling', methods=['POST','GET'])
def selling():
    if not session.get("name"):
        return redirect('/name')

    condition = request.form.get("selected_s_par")
    subcondition = request.form.get("selected_s_cat")

    title = request.form.get("atitle")
    name = request.form.get("pname")
    des = request.form.get("pdes")
    qty = request.form.get("qty")
    price = request.form.get("rprice")
    max = request.form.get("max")

    select_status=request.form.get("selected_status")

    if select_status == "option_0":
        status = 0
    if select_status == "option_1":
        status = 1


    valid = valid_category(condition,subcondition)


    if valid:
        all_listing_id = get_listing()

        new_listing = random.randint(1, 999999999)

        k = 0
        while k in range(len(all_listing_id)):
            if all_listing_id[k][0] == new_listing:
                new_listing = random.randint(1, 999999999)
                k = 0
            else:
                k+=1

        newprice = str(price)
        textprice = "$"+newprice
        new_auction(session.get("name"),new_listing,subcondition,title,name,des,qty,textprice,max,status)
        return render_template('create_sale_success.html')
    else:
        return render_template('create_sale_fail.html')

#shows seller's purchase and income history
@app.route('/seller_transaction_history', methods=['POST','GET'])
def sth():
    if not session.get("name"):
        return redirect('/name')

    user_transaction = get_transaction_info_bidder(session.get("name"))
    user_sold_transaction = get_transaction_info_seller(session.get("name"))
    return render_template('seller_transaction_history.html', user_transaction=user_transaction, user_sold_transaction=user_sold_transaction)

#show item that are sold
@app.route('/sold_notification', methods=['POST','GET'])
def snoti():
    if not session.get("name"):
        return redirect('/name')

    status = "PAID"
    status2 = "NOT PAID"

    wins_paid = get_sold(session.get("name"), status)
    wins_not_paid = get_sold(session.get("name"), status2)

    return render_template('sale_notification.html', wins_paid=wins_paid, wins_not_paid=wins_not_paid)

#for sellers to manage all their products
@app.route('/inactive_sales', methods=['POST','GET'])
def manage_sales():
    if not session.get("name"):
        return redirect('/name')

    show_0 = get_all_active_sales_seller(session.get("name"))
    show_1 = get_all_inactive_sales_seller(session.get("name"))

    return render_template('sale_manager.html', show_0=show_0, show_1=show_1)

#change status of sale to inactive
@app.route('/turn_off', methods=['POST','GET'])
def off_sales():
    if not session.get("name"):
        return redirect('/name')

    status = 0
    off_id = request.form.get("ofid")

    update_listing_status_seller(session.get("name"),off_id,status)
    update_bidders(session.get("name"),off_id)

    show_0 = get_all_active_sales_seller(session.get("name"))
    show_1 = get_all_inactive_sales_seller(session.get("name"))

    return render_template('sale_manager.html', show_0=show_0, show_1=show_1)

#change status of sale to active
@app.route('/turn_on', methods=['POST','GET'])
def on_sales():
    if not session.get("name"):
        return redirect('/name')

    status = 1
    on_id = request.form.get("onid")

    update_listing_status_seller(session.get("name"), on_id, status)

    show_0 = get_all_active_sales_seller(session.get("name"))
    show_1 = get_all_inactive_sales_seller(session.get("name"))

    return render_template('sale_manager.html', show_0=show_0, show_1=show_1)

#select action on the first page
@app.route('/select', methods=['POST','GET'])
def select():
    error = None
    choice = request.form.get("page_select")
    if choice == "empty":
        return render_template('index.html', error=error)
    if choice == "option_1":
        return render_template('login_page.html', error=error)
    if choice == "option_2":
        return render_template('User Registration.html', error=error)

#login page, user can select account type and also enter login info
@app.route('/name', methods=['POST', 'GET'])
def name():
    error = None
    session["name"] = None
    session["user_role"] = None
    if request.method == 'POST':
        selection = 0 #(0 for bidder, 1 for seller, 3 for helpdesk)
        role = request.form.get("role")
        if role == "option_1":
            selection = 0
        if role == "option_2":
            selection = 1
        if role == "option_4":
            selection = 3

        curinput = request.form['Username']
        salt_value = salt(curinput)
        if salt_value:
            salted = bcrypt.hashpw(request.form['Password'].encode('utf-8'), salt_value[0][0])
            result = valid_name(request.form['Username'], salted)
        else:
            error = 'Either username or password is incorrect'
            return render_template('Incorrect_login.html', error=error)
        if result:
            if selection == 0:
                authorized_0 = checkbidder(curinput)
                if authorized_0:
                    session["name"] = curinput
                    session["user_role"] = 0
                    return render_template('bidder_page.html', error=error, result=result)
                else:
                    error = 'invalid role'
                    return render_template('Incorrect_login.html', error=error)
            if selection == 1:
                authorized_1 = checkseller(curinput)
                if authorized_1:
                    authorized_2 = checkvendor(curinput)
                    if authorized_2:
                        session["name"] = curinput
                        session["user_role"] = 2
                        balance = get_seller_balance(curinput)
                        return render_template('vendor_page.html', error=error, result=result, balance=balance)
                    else:
                        session["name"] = curinput
                        session["user_role"] = 1
                        balance = get_seller_balance(curinput)
                        return render_template('seller_page.html', error=error, result=result, balance=balance)
                else:
                    error = 'invalid role'
                    return render_template('Incorrect_login.html', error=error)
            if selection == 3:
                authorized_3 = checkhelper(curinput)
                if authorized_3:
                    session["name"] = curinput
                    session["user_role"] = 3
                    position = get_position_help_desk(curinput)
                    return render_template('help_desk_page.html', error=error, result=result, position=position)
                else:
                    error = 'invalid role'
                    return render_template('Incorrect_login.html', error=error)
        else:
            error = 'invalid login'
            return render_template('Incorrect_login.html',error=error)
    return render_template('login_page.html', error=error)

#register account, this page is still under development
@app.route('/register', methods=['POST', 'GET'])
def register():
    error = None
    if request.method == 'POST':

        selection = 0  # (0 for bidder, 1 for seller, 2 for helpdesk)
        role = request.form.get("role")
        if role == "option_1":
            selection = 0
        if role == "option_2":
            selection = 1
        if role == "option_3":
            selection = 2
        if role == "option_4":
            selection = 3

        try:
            tempsalt = None
            username = request.form['Username']
            new_password = request.form['Password']
            invalid = valid_name(username,new_password)
            if invalid:
                error = 'User already exists'
                return render_template('Registration_failure.html', error=error)
            else:
                registration(username, new_password, tempsalt)
                saltvalue = bcrypt.gensalt()
                encodevalue = new_password.encode('UTF-8')
                addsomesalt(username,new_password,saltvalue)
                hashed_password = bcrypt.hashpw(encodevalue, saltvalue)
                updatesalt(username,hashed_password)
                return render_template('Registration_success.html', error=error)
        except:
            error = 'invalid input'
            return render_template('Registration_failure.html', error=error)
    return render_template('User Registration.html', error=error)



        #login success popup, and have a button that guides to home page or login page

        #we need to choose either the account is created for seller, bidder, or helpdesk
        #we can assume that all seller, biider, and helpdesk are within user

        #how to enter personal info for registration if user is seller,helpdesk, or just bidder?



# hashing input example
#reqpassword = request.form['Password']
#newpass = reqpassword.encode('utf-8')
#salt = bcrypt.gensalt()  USE THIS FOR REGISTER PAGE!!!!!!!!!
#hashed_password = bcrypt.hashpw(newpass, salt)
#result = valid_name(request.form['Username'], hashed_password)

#implement able to hash while using the application

#When implementing register page, make sure to add to salt column for new passwords

@app.route('/struggle', methods=['POST', 'GET'])
def struggle():
    error = None
    if request.method == 'POST':
        result = delete_name(request.form['Firstname'], request.form['LastName'])
        if result:
            return render_template('delete.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('delete.html', error=error)

def exist_payment(email):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS credit_cards(credit_card_num TEXT PRIMARY KEY NOT NULL, card_type TEXT NOT NULL, expire_month INTEGER NOT NULL, expire_year INTEGER NOT NULL, security_code INTEGER NOT NULL, owner_email TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM credit_cards WHERE owner_email=?;',(email,))
    return cursor.fetchall()

def local_vendor_info(email):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS local_vendors(email TEXT PRIMARY KEY NOT NULL, business_name TEXT NOT NULL, business_address_id TEXT NOT NULL, customer_service_phone_number TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM local_vendors WHERE email=?;',(email,))
    return cursor.fetchall()

def get_bank_info (email):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS sellers(email TEXT PRIMARY KEY NOT NULL, bank_routing_number TEXT NOT NULL, bank_account_number TEXT NOT NULL, balance INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM sellers WHERE email=?;',(email,))
    return cursor.fetchall()

def get_zipcode_info (zipcode):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS zipcode_info(zipcode INTEGER PRIMARY KEY NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM zipcode_info WHERE zipcode=?;', (zipcode,))
    return cursor.fetchall()

def get_address_info(address_id):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS address(address_id TEXT PRIMARY KEY NOT NULL, zipcode INTEGER NOT NULL, street_num INTEGER NOT NULL, street_name TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM address WHERE address_id = ?;', (address_id,))
    return cursor.fetchall()

def get_bidder_info(email):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS bidders(email TEXT PRIMARY KEY NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL, gender TEXT NOT NULL, age INTEGER NOT NULL, home_address_id TEXT NOT NULL, major TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM bidders WHERE email = ?;',(email,))
    return cursor.fetchall()


def get_position_help_desk(account):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS helpdesk(email TEXT PRIMARY KEY NOT NULL, position TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT position FROM helpdesk WHERE email =?;', (account,))
    return cursor.fetchall()

def get_balance_seller(seller):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS sellers(email TEXT PRIMARY KEY NOT NULL, bank_routing_number TEXT NOT NULL, bank_account_number TEXT NOT NULL, balance INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT balance FROM sellers WHERE email = ?;',(seller,))
    return cursor.fetchall()

def get_transaction_info_seller(seller):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS transactions(transaction_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, date TEXT NOT NULL, payment INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT transaction_id, bidder_email, listing_id, date, payment FROM transactions WHERE seller_email = ?;',(seller,))
    return cursor.fetchall()

def get_sold(seller,status):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS winner(listing_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT PRIMARY KEY NOT NULL, bidder_email TEXT PRIMARY KEY NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, description TEXT, quantity INTEGER NOT NULL, sold_price INTEGER NOT NULL, paid_status TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT listing_id, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status FROM winner WHERE seller_email = ? AND paid_status = ?;',(seller, status))
    return cursor.fetchall()

def update_bidders(seller,id):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS bids(bid_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, bid_price INTEGER NOT NULL);')
    connection.execute('DELETE FROM bids WHERE seller_email=? AND listing_id=?;',(seller,id))
    connection.commit()


def update_listing_status_seller(seller,id,status):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.execute('UPDATE auction_listing SET status=? WHERE seller_email=? AND listing_id=?;',(status,seller,id))
    connection.commit()

def get_all_active_sales_seller(seller):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE seller_email=? AND status = 1;',(seller,))
    return cursor.fetchall()

def get_all_inactive_sales_seller(seller):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE seller_email=? AND status = 0;',(seller,))
    return cursor.fetchall()

def get_listing():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT listing_id FROM auction_listing;')
    return cursor.fetchall()

def new_auction(seller,listing,cate,title,name,desc,qty,r_price,max,status):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.execute('INSERT INTO auction_listing(seller_email,listing_id,category,auction_title,product_name,product_description,quantity,reserve_price,max_bids,status) VALUES (?,?,?,?,?,?,?,?,?,?);',(seller,listing,cate,title,name,desc,qty,r_price,max,status))
    connection.commit()


def valid_category(par,child):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS categories(parent_category TEXT NOT NULL, category_name TEXT PRIMARY KEY NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM categories WHERE parent_category = ? AND category_name = ?;',(par,child))
    return cursor.fetchall()

def get_transaction_info_bidder(bidder):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS transactions(transaction_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, date TEXT NOT NULL, payment INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT transaction_id, seller_email, listing_id, date, payment FROM transactions WHERE bidder_email = ?;',(bidder,))
    return cursor.fetchall()

def update_transaction_history(transaction_id, seller, listing, bidder, date, payment):
    connection=sql.connect('database.db')
    connection.execute('INSERT INTO transactions(transaction_id,seller_email,listing_id,bidder_email,date,payment) VALUES (?,?,?,?,?,?);',(transaction_id, seller, listing, bidder, date, payment))
    connection.commit()

def get_transaction_id():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS transactions(transaction_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, date TEXT NOT NULL, payment INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT transaction_id FROM transactions;')
    return cursor.fetchall()

def update_seller_balance(seller,balance):
    connection=sql.connect('database.db')
    connection.execute('UPDATE sellers SET balance = ? WHERE email = ?;', (balance,seller))
    connection.commit()

def get_seller_balance(seller):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS sellers(email TEXT PRIMARY KEY NOT NULL, bank_routing_number TEXT NOT NULL, bank_account_number TEXT NOT NULL, balance INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT balance FROM sellers WHERE email=?;',(seller,))
    return cursor.fetchall()

def update_winner_paid_status(bidder,listing,seller,status):
    connection=sql.connect('database.db')
    connection.execute('UPDATE winner SET paid_status = ? WHERE bidder_email = ? AND listing_id = ? AND seller_email = ?;',(status,bidder,listing,seller))
    connection.commit()

def get_price_winner(email, listing):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS winner(listing_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT PRIMARY KEY NOT NULL, bidder_email TEXT PRIMARY KEY NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, description TEXT, quantity INTEGER NOT NULL, sold_price INTEGER NOT NULL, paid_status TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT seller_email, sold_price FROM winner WHERE bidder_email = ? AND listing_id = ?;',(email, listing))
    return cursor.fetchall()

def update_winner(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status):
    connection=sql.connect('database.db')
    connection.execute('INSERT INTO winner(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status) VALUES (?,?,?,?,?,?,?,?,?);',(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status))
    connection.commit()

def get_winner(bidder,status):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS winner(listing_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT PRIMARY KEY NOT NULL, bidder_email TEXT PRIMARY KEY NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, description TEXT, quantity INTEGER NOT NULL, sold_price INTEGER NOT NULL, paid_status TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT listing_id, seller_email, auction_title, product_name, description, quantity, sold_price, paid_status FROM winner WHERE bidder_email = ? AND paid_status = ?;',(bidder, status))
    return cursor.fetchall()

def check_credit(num):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS credit_cards(credit_card_num TEXT PRIMARY KEY NOT NULL, card_type TEXT NOT NULL, expire_month INTEGER NOT NULL, expire_year INTEGER NOT NULL, security_code INTEGER NOT NULL, owner_email TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT credit_card_num FROM credit_cards WHERE credit_card_num = ?;',(num,))
    return cursor.fetchall()

def add_credit(num,type,month,year,code,user):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS credit_cards(credit_card_num TEXT PRIMARY KEY NOT NULL, card_type TEXT NOT NULL, expire_month INTEGER NOT NULL, expire_year INTEGER NOT NULL, security_code INTEGER NOT NULL, owner_email TEXT NOT NULL);')
    connection.execute('INSERT INTO credit_cards(credit_card_num, card_type, expire_month, expire_year, security_code, owner_email) VALUES (?,?,?,?,?,?);',(num,type,month,year,code,user))
    connection.commit()
    cursor = connection.execute('SELECT credit_card_num, card_type, expire_month, expire_year, security_code FROM credit_cards WHERE owner_email = ?;',(user,))
    return cursor.fetchall()

def find_credit(user):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS credit_cards(credit_card_num TEXT PRIMARY KEY NOT NULL, card_type TEXT NOT NULL, expire_month INTEGER NOT NULL, expire_year INTEGER NOT NULL, security_code INTEGER NOT NULL, owner_email TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT credit_card_num, card_type, expire_month, expire_year, security_code FROM credit_cards WHERE owner_email = ?;',(user,))
    return cursor.fetchall()

def remove_card(card_num):
    connection=sql.connect('database.db')
    connection.execute('DELETE FROM credit_cards WHERE credit_card_num = ?;',(card_num,))
    connection.commit()

def user_ongoing_auc(user):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=1 AND listing_id IN (SELECT listing_id FROM bids WHERE bidder_email = ?);',(user,))
    return cursor.fetchall()

def user_sold_auc(user):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=2 AND listing_id IN (SELECT listing_id FROM bids WHERE bidder_email = ?);',(user,))
    return cursor.fetchall()

def update_bids(id,seller,listing,bidder,price):
    connection = sql.connect('database.db')
    connection.execute('INSERT INTO bids(bid_id,seller_email,listing_id,bidder_email,bid_price) VALUES (?,?,?,?,?);',(id,seller,listing,bidder,price))
    connection.commit()

def get_bid_id():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS bids(bid_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, bid_price INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT bid_id FROM bids')
    return cursor.fetchall()

def updatestatus(selleremail, listingid, newstatus):
    connection=sql.connect('database.db')
    connection.execute('UPDATE auction_listing SET status = ? WHERE seller_email = ? AND listing_id = ?;',(newstatus,selleremail,listingid))
    connection.commit()

def showbids(id):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS bids(bid_id INTEGER PRIMARY KEY NOT NULL, seller_email TEXT NOT NULL, listing_id INTEGER NOT NULL, bidder_email TEXT NOT NULL, bid_price INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT bid_id, bidder_email, bid_price FROM bids WHERE listing_id = ?;',(id,) )
    return cursor.fetchall()

def s_ongoing_auc(item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=1 AND product_name=?;',(item,))
    return cursor.fetchall()

def s_ended_auc(item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=0 AND product_name=?;',(item,))
    return cursor.fetchall()

def s_sold_auc(item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=2 AND product_name=?;',(item,))
    return cursor.fetchall()

def selected_product(id):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE listing_id=?;',(id,))
    return cursor.fetchall()

def ongoing_auc():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=1')
    return cursor.fetchall()

def closed_auc():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=0')
    return cursor.fetchall()

def sold_auc():
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=2')
    return cursor.fetchall()

def check_valid(parent, child):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS categories(parent_category TEXT NOT NULL, category_name TEXT PRIMARY KEY NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM categories WHERE parent_category=? AND category_name=?;',(parent,child))
    return cursor.fetchall()

def main_product_OG(condition):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=1 AND category IN (SELECT category_name FROM categories WHERE parent_category=?);', (condition,))
    return cursor.fetchall()

def main_product_FI(condition):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=0 AND category IN (SELECT category_name FROM categories WHERE parent_category=?);', (condition,))
    return cursor.fetchall()

def main_product_END(condition):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=2 AND category IN (SELECT category_name FROM categories WHERE parent_category=?);', (condition,))
    return cursor.fetchall()

def sub_product_OG(sub_item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=1 AND category = ?;',(sub_item,))
    return cursor.fetchall()

def sub_product_FI(sub_item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=0 AND category = ?;',(sub_item,))
    return cursor.fetchall()

def sub_product_END(sub_item):
    connection=sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS auction_listing(seller_email TEXT PRIMARY KEY NOT NULL, listing_id INTEGER PRIMARY KEY NOT NULL, category TEXT NOT NULL, auction_title TEXT NOT NULL, product_name TEXT NOT NULL, product_description TEXT NOT NULL, quantity INTEGER NOT NULL, reserve_price TEXT NOT NULL, max_bids INTEGER NOT NULL, status INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM auction_listing WHERE status=2 AND category = ?;',(sub_item,))
    return cursor.fetchall()

def cat_name(parent):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS categories(parent_category TEXT NOT NULL, category_name TEXT PRIMARY KEY NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT category_name FROM categories WHERE parent_category=?;', (parent,))
    return cursor.fetchall()

def sub_cat_name():
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS categories(parent_category TEXT NOT NULL, category_name TEXT PRIMARY KEY NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT category_name FROM categories;')
    return cursor.fetchall()

def parent_cat():
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS categories(parent_category TEXT NOT NULL, category_name TEXT PRIMARY KEY NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT DISTINCT parent_category FROM categories;')
    return cursor.fetchall()

def checkbidder(user_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS bidders(email TEXT PRIMARY KEY NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL, gender TEXT NOT NULL, age INTEGER NOT NULL, home_address_id TEXT NOT NULL, major TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT email FROM bidders WHERE email = ?;',(user_name,))
    return cursor.fetchall()

def checkseller(user_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS sellers(email TEXT PRIMARY KEY NOT NULL, bank_routing_number TEXT NOT NULL, bank_account_number TEXT NOT NULL, balance INTEGER NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT email FROM sellers WHERE email = ?;',(user_name,))
    return cursor.fetchall()

def checkvendor(user_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS local_vendors(email TEXT PRIMARY KEY NOT NULL, business_name TEXT NOT NULL, business_address_id TEXT NOT NULL, customer_service_phone_number TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT email FROM local_vendors WHERE email = ?;',(user_name,))
    return cursor.fetchall()

def checkhelper(user_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS helpdesk(email TEXT PRIMARY KEY NOT NULL, position TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT email from helpdesk WHERE email = ?;',(user_name,))
    return cursor.fetchall()

def salt(user_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT salt FROM users WHERE username = ?;', (user_name,))
    return cursor.fetchall()


def valid_name(user_name, pass_word):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT username, password FROM users WHERE username = ? AND password = ?;', (user_name, pass_word))
    return cursor.fetchall()

def registration(user_name,pass_word,tempsalt):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL);')
    connection.execute('INSERT INTO users (username, password,salt) VALUES (?,?,?);', (user_name, pass_word,tempsalt))
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()

def addsomesalt (user_name, pass_word, saltvalue):
    connection = sql.connect('database.db')
    connection.execute('UPDATE users SET salt = ? WHERE username = ? AND password = ? ', (saltvalue,user_name,pass_word))
    connection.commit()

def updatesalt (username,hashed_password):
    connection = sql.connect('database.db')
    connection.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
    connection.commit()

def delete_name(user_name, pass_word):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL);')
    connection.execute('DELETE FROM users WHERE username =? AND password =?;', (user_name, pass_word))
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()

def current():
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL);')
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()

if __name__ == "__main__":
    app.run()


