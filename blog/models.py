from blog import app
from flask import Flask
#from pymongo.objectid import Object
#from pymongo import Connection
#import json
#import redis
#from mongokit import Document
#r = redis.Redis(host='localhost',port=6379,db=0)
#connection = Connection('localhost', 27017)
#db = connection['blog']
#collection = db.collection

#class User(Document):
    #structure = { 'email': unicode,
                  #'pw_hash':unicode, 
                  #'confirmed':bool,
                  #'created_at': datetime.datetime,
                  #'token':unicode }

    #@staticmethod
    #def get_by_email(email):
        #users = connection['blog'].users
        #return users.User.find_one({email:email})

    #@staticmethod
    #def register_new_user(email, password):
      #users = connection['blog'].users
      #newuser = users.User()
      #newuser.email = unicode(email)
      #newuser.set_password(password);
      #newuser.confirmed = False;
      #newuser.created_at = datetime.datetime.now()
      #newuser.token = unicode(generateRandomToken(48));
      #newuser.save();
      #return newuser;

    #def set_password(self,password):
        #self.pw_hash = unicode(generate_password_hash(password))

    #def check_password(self,password):
        #return check_password_hash(self.pw_hash, unicode(password))

    #use_dot_notation = True
    #def __repr__(self):
        #return '<User %r>' % (self.email)

