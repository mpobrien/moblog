#!/usr/bin/env python
from blog import app
import os
app.debug = True
if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5001))
  app.run(port=port,host='0.0.0.0')
