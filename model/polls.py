from collections import Counter
from tinydb import Query
import hashlib,binascii
import os
class poll(object):
    def __init__(self,infos,eid=None):
        self.infos = infos
        if not "candidats" in self.infos.keys() : 
            self.infos["candidats"]= []
        if not "votes" in self.infos.keys() :
            self.infos["votes"] = []
        self.eid = eid
    def getName(self):
        return self.infos["name"]
    def getCandidats(self):
        return self.infos["candidats"]
    def add_candidat(self,candidat):
        self.infos["candidats"].append(int(candidat))

    def add_vote(self,vote):
        self.infos["votes"].append(vote)

    def result(self):
        return [ (x,y) for x,y in Counter(self.infos["votes"]).items() ]
    
    def save(self,db):
        if self.eid :
            db.update(self.infos,eids=[self.eid])
        else :
            self.eid = db.insert(self.infos)
        
def getAll(db):
    return [ poll(x,x.eid) for x in db.all() ] 


def getOnebyName(name,db):
    query = Query()
    poll_returned=db.get(query.name == name )
    return poll(poll_returned,poll.eid)
