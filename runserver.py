#!/usr/bin/env python
from blog import app
app.debug = True
if __name__ == '__main__':
  app.run(port=80,host='0.0.0.0')
