import sys
import os 
import ujson
from tinydb import TinyDB,Query
import hashlib,binascii
from collections import Counter
from flask import Flask,request,render_template,redirect,url_for
from model import users, polls
from utils.mail import send_mail
import codecs


app = Flask(__name__)
db = TinyDB('db.db')
keys_db = db.table("credentials")
peoples_db = db.table("peoples")
polls_db = db.table("polls")

@app.route("/")
def racine():
    if len(peoples_db.all()) == 0 :
        return redirect(url_for('init'))
    else : 
        return render_template("login.html",routing=url_for("vote"))

@app.route("/vote",methods=["POST"])
def vote():
    password = request.form["password"]
    query = Query()
    is_admin = keys_db.get(query.admin_password == hashlib.sha256(password).hexdigest())
    if is_admin:
        polls_list = []
        for poll in polls.getAll(polls_db):
            polls_list.append( (poll.getName(),poll.result()) )

        users_by_eid = users.getAllByEid(peoples_db)
        query = Query()
        nb_votant = users.nb_votant(peoples_db)
        return render_template("admin.html", polls=polls_list, peoples=users.getAll(peoples_db),peoples_byeid=users_by_eid,nb_votant=nb_votant)
    query = Query()
    voter = users.getOneByPass(peoples_db,password)
    if voter:
        if not voter.getVoted():
           users_dict = users.getAllByEid(peoples_db)
           return render_template("do_vote.html",
                                   polls=polls.getAll(polls_db), action=url_for("process_vote"),users=users_dict,user=voter)
        else:
            return render_template("already_voted.html")
    return redirect(url_for("racine"))

@app.route("/process",methods=["POST"])
def process_vote():
    for poll in polls.getAll(polls_db):
        votes = request.form.getlist(poll.getName())
        if votes :
            [ poll.add_vote(int(x)) for x in votes]
        poll.save(polls_db)
    query = Query()
    print request.form["user"]
    voter = users.getOneByEid(peoples_db,int(request.form["user"]))
    print voter
    voter.vote()
    voter.save(peoples_db)
    return redirect(url_for("racine"))

@app.route("/init", methods=["GET"])
def init():
    query=Query()
    set_key = keys_db.search(query.key == 'set_key')
    init_key = binascii.hexlify(os.urandom(10))
    keys_db.insert({ "key":"init_key", "value": init_key})

    seted_candidates = keys_db.search(query.key == "candidates_set")
    if len(set_key) == 0 :
        keys_db.insert({ "key":"salt", "value": binascii.hexlify(os.urandom(20))})
        return render_template('init.html',init_key=init_key,set_init_url=url_for("set_init"))
    elif len(set_key) > 0 and len(seted_candidates) == 0 :
        return render_template('set_candidates.html',action=url_for("set_candidates"),users=users.getAllByEid(peoples_db),polls=polls.getAll(polls_db))
    else:
        return redirect(url_for("racine"))

@app.route("/set_candidates",methods=["POST"])
def set_candidates() :
    polls_list=polls.getAll(polls_db)
    users_list=users.getAll(peoples_db)
    for poll in polls_list:
        candidates = request.form.getlist(poll.getName())
        for candidat in candidates:
            poll.add_candidat(candidat)
        poll.save(polls_db)

    seted_candidates = binascii.hexlify(os.urandom(10))
    keys_db.insert({ "key":"candidates_set", "value": seted_candidates})
    return redirect(url_for("racine"))
    
@app.route("/purge")
def purge():
    db.purge()
    print users_list
    db.purge_tables()
    return " done"


@app.route("/set_init", methods=["POST"])
def set_init():
    query = Query()
    salt = keys_db.get(query.key == "salt")["value"]
    query = Query()
    init_key = keys_db.get((query.key == "init_key") & (query.value == request.form["password"] ) )
    if init_key == None:
        raise ValueError(" form not conforme are you attacking me ?") 

    voters = request.form["voters"].split("\n") # list of people who votes
    elections = request.form["elections"].strip().split("\n") # list of elections 

    keys_db.insert({"admin_password" : hashlib.sha256(request.form["admin_password"]).hexdigest()})# save admin_pass

    for election in elections :
        poll_tmp = polls.poll({"name" : election.strip()})
        poll_tmp.save(polls_db)

    for elector in voters :
        people = elector.strip().split(";")
        user_tmp = users.user({"name" : people[0],"surname" : people[1], "email" : people[2] })
        user_tmp.save(peoples_db)
    set_key = binascii.hexlify(os.urandom(10))
    keys_db.insert({ "key":"set_key", "value": set_key})

    return redirect(url_for("init"))

@app.route("/mail/<int:id>")
def mail(id):
    print id
    dest=users.getOneByEid(peoples_db,id)
    mail_config = ujson.load(open("mail_config.json"))
    send_mail(mail_config["content"].format(dest.getCode()),mail_config["addresse"],dest.getEmail(),mail_config["server"],mail_config["login"],mail_config["password"])
    return redirect(url_for("racine"))

if __name__ == "__main__":
    app.run(debug=True)

