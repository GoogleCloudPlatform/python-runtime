"""The hello world flex app!"""

import webapp2


class HelloHandler(webapp2.RequestHandler):

  def get(self):
    msg = 'Hello GAE Flex (env: flex) Compat-Runtime App\n'
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(msg)

app = webapp2.WSGIApplication([('/', HelloHandler)],
                              debug=True)
