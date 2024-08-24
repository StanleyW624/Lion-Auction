from flask import Flask, render_template, request
import sqlite3 as sql
import bcrypt


def maketable():

    all_listing = find_sold()
    all_transaction = total_trans()

    print(len(all_listing))
    print(len(all_transaction))

    for i in range(len(all_listing)):
        paid_status = "NOT PAID"
        current_bids = showbids(all_listing[i][0])
        current_highest  = current_bids[0][2]
        bidder_email = current_bids[0][1]

        for k in range(len(current_bids)):
            if (current_bids[k][2] > current_highest):
                current_highest = current_bids[k][2]
                bidder_email = current_bids[k][1]

        sold_price = current_highest

        status = check_status(all_listing[i][1],all_listing[i][0],bidder_email)

        if status:
            paid_status = "PAID"

        newtable(all_listing[i][0],all_listing[i][1],bidder_email,all_listing[i][2],all_listing[i][3],all_listing[i][4],all_listing[i][5],sold_price,paid_status)

def total_trans():
    connection=sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM transactions;')
    return cursor.fetchall()

def check_status(seller, id, bidder):
    connection=sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM transactions WHERE seller_email = ? AND listing_id = ? AND bidder_email = ?;', (seller, id, bidder))
    return cursor.fetchall()

def showbids(id):
    connection=sql.connect('database.db')
    cursor = connection.execute('SELECT bid_id, bidder_email, bid_price FROM bids WHERE listing_id = ?;',(id,) )
    return cursor.fetchall()

def find_sold():
    connection=sql.connect('database.db')
    cursor = connection.execute('SELECT listing_id, seller_email, auction_title, product_name, product_description, quantity FROM auction_listing WHERE status=2')
    return cursor.fetchall()

def newtable(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status):
    connection=sql.connect('database.db')
    connection.execute('INSERT INTO winner(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status) VALUES (?,?,?,?,?,?,?,?,?);',(listing_id, seller_email, bidder_email, auction_title, product_name, description, quantity, sold_price, paid_status))
    connection.commit()



maketable()

app = Flask(__name__)
if __name__ == "__main__":
    app.run()