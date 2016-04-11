from tinydb import Query
import hashlib,binascii
import os
class user(object):
    def __init__(self,infos,eid=None):
        self.infos = infos
        if "type" not in self.infos.keys():
            self.infos["type"] = "user"
        if "voted" not in self.infos.keys():
            self.infos["voted"] = 0
        if "status" not in self.infos.keys():
            self.infos["status"] = 0
        if "code" not in self.infos.keys():
            self.infos["code"] = self.infos["name"][0]+self.infos["surname"][:3]+binascii.hexlify(os.urandom(1))
        self.eid = eid
    def getName(self):
        return self.infos["name"]
    def getSurname(self):
        return self.infos["surname"]
    def getEmail(self):
        return self.infos["email"]
    def getVoted(self):
        return self.infos["voted"]
    def vote(self):
        self.infos["voted"] = 1
    def getCode(self):
        return self.infos["code"]
    def resetCode(self):
        self.infos["code"] = self.infos["name"][0]+self.infos["surname"][:3]+binascii.hexlify(os.urandom(2))
        return self.infos["code"]

    def save(self,db):
        if not self.eid :
            self.eid=db.insert(self.infos)
        else:
            db.update(self.infos,eids=[self.eid])
            
def getOneByEid(db,eid):
    user_tmp = db.get(eid=eid)
    if user_tmp :
        return user(user_tmp,user_tmp.eid)
def getOneByPass(db,passwd):
    query = Query()
    voter = db.get(query.code == passwd)
    if voter :
        return user(voter,voter.eid)
def getAll(db):
     return [ user(x,x.eid) for x in db.all() ]
def getAllByEid(db):
    users_list = [ (x.eid,user(x,x.eid)) for x in db.all() ]
    users = {key: value for (key, value) in users_list  }
    return users

def nb_votant(db):
    query = Query()
    return len(db.search(query.voted==1))
