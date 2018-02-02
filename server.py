import csv,sqlite3,pymysql,requests,ast,pprint,sys,os,json,datetime,time
pymysql.install_as_MySQLdb()
import MySQLdb
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "mysql://kk126203:12345678@oa.crvapzhaz69x.us-east-1.rds.amazonaws.com:3306/event"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None



@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


def process_t(s):
  if len(s)==1:
    return "0"+s
  else:
    return s


def process_d(s):
  if s=="today":
    return 1
  elif s=="tomorrow":
    return 2
  elif s=="next one week":
    return 7
  else:
    return 30

@app.route('/')
def homepage():
  return render_template("homepage.html")

graph = {}
graph['Auditorium'] = "https://images.adsttc.com/media/images/5912/4b1b/e58e/ce33/1000/0611/large_jpg/011.jpg?1494371094"
graph['Gymnastic_Room'] = "http://columbiagymnastics.com/wp-content/uploads/2017/05/image-6_small.jpg"
graph['Banard_Hall'] = "http://images.bwog.com/wp-content/uploads/2015/04/reid_hall.jpg"
graph['Uris_Library'] = "https://olinuris.library.cornell.edu/sites/default/files/user3/ADW_color_AES.jpg"
graph['Basketball_Field'] = "http://shop.wilson.com/media/catalog/product/cache/38/image/9df78eab33525d08d6e5fb8d27136e95/w/t/wtb0516r-1.jpg"
graph['Law_Building'] = "https://c1.staticflickr.com/7/6175/6167794285_b25c3e76b9_b.jpg"
graph['Business_Center'] = "https://cdngeneral.rentcafe.com/dmslivecafe/3/470410/Business_Center.jpg?crop=(0,0,300,200)&cropxunits=300&cropyunits=200&quality=85&width=956&height=637&mode=crop"
graph['Dance_Center'] = "https://s3-media4.fl.yelpcdn.com/bphoto/S6kPtyU-CTYBgVBJaBfzrQ/ls.jpg"


@app.route('/do_query', methods=['POST'])
def do_query():
  start_time = time.time()
  events = request.form['events']
  location = request.form['location']
  date = request.form['date']
  now = datetime.datetime.now()
  start = process_t(str(now.year))+process_t(str(now.month))+process_t(str(now.day))
  delta = process_d(str(date))
  end = now+datetime.timedelta(days=delta)
  end = process_t(str(end.year))+process_t(str(end.month))+process_t(str(end.day))

  if len(events)==0:
    q = "select * from "+location+" where start >= "+start+" and end <= "+end+" and year(start)>0 order by start "
  else:
    q = "select * from "+location+" where description like '%%%%"+events+"%%%%'"

  m = str(q)
  cursor = g.conn.execute(m)
  a = []
  for index in cursor :
    b = []
    b.append(str(index['start']))
    b.append(str(index['end']))
    b.append(str(index['club']))
    b.append(str(index['description']))
    a.append(b)

  time_passed = time.time()-start_time
  context = dict(data = a, data2 = location, data3 = len(a), data4 = time_passed, data5 = graph[location])
  return render_template("respond1.html", **context)


@app.route('/add')
def add():
  return render_template("add1.html")


def convert_int(s):
  try:
    a = int(s)
    return a
  except:
    return -1


@app.route('/do_add', methods=['POST'])
def do_add():
  location = request.form['location']
  print location
  month = request.form['month']
  day1 = request.form['day']
  start1 = request.form['start']
  end1 = request.form['end']
  description = request.form['events']
  club = request.form['club']
  if len(day1)==0 or len(start1)==0 or len(end1)==0:
    context = dict(data = "Some information were lost, plz try again", )
    return render_template("error.html", **context)
  
  day = convert_int(day1)
  start = convert_int(start1)
  end = convert_int(end1)
  if day==-1 or start==-1 or end==-1:
    context = dict(data = "Invalid format, plz input integer", )
    return render_template("error.html", **context)

  if start>=end :
    context = dict(data = "End time should be later than start time, plz try again", )
    return render_template("error.html", **context)

  if day>31 or day<=0:
    context = dict(data = "Invalid date, plz try again", )
    return render_template("error.html", **context)

  if start>22 or start<10 or end>22 or end<10:
    context = dict(data = "We are not opening at that time, plz try again", )
    return render_template("error.html", **context)
  
  now = datetime.datetime.now()
  today = "2018-"+process_t(str(now.month))+"-"+process_t(str(now.day))
  tmp = now+datetime.timedelta(days=1)
  tomorrow = "2018-"+process_t(str(tmp.month))+"-"+process_t(str(tmp.day))
  
  command1 = "select * from "+location+" where start>'"+today+"' and end<'"+tomorrow+"' and club = '"+club+"'"
  
  exist = g.conn.execute(command1)
  i = 0
  for index in exist:
    i = i+1
  if i>0:
    context = dict(data = "Your Club has already booked an event in the ", data1 = location, data2 = " at ", data3 = str(today), data4 = " so please choose another day, thx")
    return render_template("dup.html", **context)
  
  if int(month)<now.month or day<now.day:
    context = dict(data = "Please input a day that is later than today", data1 = today)
    return render_template("error.html", **context)

  command2 = "select * from "+location+" where hour(end)<="+end1+" and hour(end)>"+start1+" or hour(start)>="+start1+" and hour(start)<"+end1+" or hour(end)>="+end1+" and hour(start)<="+start1+" and start>'"+today+"' and end<'"+tomorrow+"'"
  room = g.conn.execute(command2)
  print command2
  j=0
  for index in room:
    j+=1
  if j>=3:
    context = dict(data = "There're no available rooms in this time slots, We apologize for the inconvenience.")
    return render_template("error.html", **context)

  start_h = "2018"+'-'+process_t(month)+'-'+process_t(day1)+" "+process_t(start1)
  end_h = "2018"+'-'+process_t(month)+'-'+process_t(day1)+" "+process_t(end1)

  
  q = "insert into "+location+" (start, end, club, description) values ('"+start_h+"', '"+end_h+"', '"+club+"', '"+description+"')"
  cursor = g.conn.execute(q)
  print q
  
  return render_template("done.html")



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

  run()



