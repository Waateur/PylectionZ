import sys
import os 
from tinydb import TinyDB,Query
import hashlib,binascii

from flask import Flask,request,render_template,redirect,url_for

app = Flask(__name__)
db = TinyDB('db.db')
@app.route("/")
def racine():
    keys = db.table("credentials")
    peoples = db.table("peoples")
    polls = db.table("polls")
    if len(peoples.all()) == 0 :
        return redirect(url_for('init'))
    else : 
        return render_template("login.html",routing=url_for("vote"))

@app.route("/vote",methods=["POST"])
def vote():
    keys = db.table("credentials")
    peoples = db.table("peoples")
    polls = db.table("polls")
    password = request.form["password"]
    query = Query()
    is_admin = keys.get(query.admin_password == hashlib.sha256(password).hexdigest())
    if is_admin:
        return render_template("admin.html", polls=polls.all(), peoples=peoples.all())
    query = Query()
    voter = peoples.get(query.code == password)
    if voter:
        print voter["voted"]
        if not voter["voted"]:
           users_list = [(x.eid,"{} {}".format(x["name"],x["surname"])) for x in peoples.all()]
           users = {key: value for (key, value) in users_list  }
           return render_template("do_vote.html",
                                   polls=polls.all(), action=url_for("process_vote"),users=users,passcode=voter["code"])
        else:
            return render_template("already_voted.html")
    return redirect(url_for("racine"))

@app.route("/process",methods=["POST"])
def process_vote():
    keys = db.table("credentials")
    peoples = db.table("peoples")
    polls = db.table("polls")

    polls_key=request.form.keys()[:-1]
    for poll_name in polls_key:
        votes = request.form.getlist(poll_name)
        query = Query()
        apoll = polls.get(query.poll == poll_name)
        [apoll["votes"].append(int(x)) for x in votes]
        polls.update(apoll,eids=[apoll.eid])
    query = Query()
    voter = peoples.get(query.code ==request.form["user"])
    voter["voted"] = 1
    print voter
    peoples.update(voter,eids=[voter.eid])
    return redirect(url_for("racine"))

@app.route("/init", methods=["GET", 'POST'])
def init():
    query=Query()
    keys= db.table("credentials")
    init_key = keys.search(query.key == 'init')
    if len(init_key) == 0 or len(db) == 0:
        init_key = binascii.hexlify(os.urandom(10))
        keys.insert({ "key":"init_key", "value": init_key})
        keys.insert({ "key":"salt", "value": binascii.hexlify(os.urandom(20))})
        return render_template('init.html',init_key=init_key,set_init_url=url_for("set_init"))
    else:
        return redirect(url_for("racine"))

#    admin = db.search(query.key == 'admin')
#    if hashlib.sha256(request.form['password']).hexdigest() != admin["password"]:
#        return redirect(url_for("racine"))
#    else :
#        admin_key = binascii.hexlify(os.urandom(10))
#        keys.insert({ "key":"admin_key", "value": admin_key})
#        return render_template("init.html",admin_key=admin_key)
#


@app.route("/purge")
def purge():
    db.purge()
    db.purge_tables()
    return " done"


@app.route("/set_init", methods=["POST"])
def set_init():
    keys = db.table("credentials")
    peoples = db.table("peoples")
    polls = db.table("polls")
    
    query = Query()
    salt = keys.get(query.key == "salt")["value"]

    query = Query()
    init_key = keys.get((query.key == "init_key") & (query.value == request.form["password"] ) )
    if init_key == None:
        raise ValueError(" form not conforme are you attacking me ?") 


    voters = request.form["voters"].split("\n") # list of people who votes
    applicants = request.form["applicants"].split("\n") # list of candidates

    keys.insert({"admin_password" : hashlib.sha256(request.form["admin_password"]).hexdigest()})# save admin_pass


    categories = [ x["categorie"] for x in polls.all()]
    for peo in applicants :
        if not peo:
            continue
        people = peo.strip().split(";")
        personal_code =people[0][0]+people[1][:3]+binascii.hexlify(os.urandom(1))
        inserted_eid=peoples.insert({"name" : people[0],"surname" : people[1], "status" : 1, "categorie" : people[2], "voted" : 0, "code" : personal_code })
        if people[2] not in categories:
            categories.append(people[2])
            polls.insert({"poll":people[2],"candidates":[inserted_eid],"votes":[]})
        else :
            query=Query()
            poll= polls.get(query.poll == people[2])
            polls.update({"candidates":poll["candidates"]+[inserted_eid]},eids=[poll.eid])



    for voter in voters :
        if not voter:
            continue
        people=voter.strip().split(';')
        query = Query()
        if len(db.search( (query.name == people[0]) & (query.surname == people[1]) ) )  == 0:
            peoples.insert({"name" : people[0],"surname" : people[1], "status" : 0, "voted" : 0, "code" : people[0][0]+people[1][:3]+binascii.hexlify(os.urandom(1)) })

    keys.remove(eids=[init_key.eid])
    return redirect(url_for("racine"))



if __name__ == "__main__":
    app.run(debug=True)
