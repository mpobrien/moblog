from flask import Flask
app = Flask(__name__)
#app.debug = True
app.secret_key = '"\x97\xaa0\x87\xf3T\x95W\xeb\x1eS\xc2\x00X\x1c\xa7\'\xda\xc5\x82\xc0|\xec\xa0"'
app.admins = ['mpobrien']

#MONGODB_HOST = 'localhost'
#MONGODB_PORT = 27017

app.config.from_object(__name__)
import blog.views
import blog.models
import blog.forms
