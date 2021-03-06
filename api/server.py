from flask import Flask, request, Response, redirect
app = Flask(__name__)
import mercantile
import requests
import task
from io import BytesIO
from lxml import etree
import re

height_db = task.height_db()

@app.route("/api")
def status():
  return "OK"

# example: /api/mapillary?url=http://tiles.openmassing.org/api/sfbuildingheight_16_10491_25321.osm
@app.route("/api/mapillary")
def mapillary():
  url = request.args.get('url')
  match = re.search("sfbuildingheight_(\d+)_(\d+)_(\d+).osm",url)
  z = int(match.group(1))
  x = int(match.group(2))
  y = int(match.group(3))
  bb = mercantile.bounds(x,y,z)
  centroid = [(bb.west + bb.east) / 2, (bb.north + bb.south) / 2]
  return redirect("https://www.mapillary.com/app/?lat={0}&lng={1}&z={2}".format(centroid[1],centroid[0],z))

# example: /api/sfbuildingheight_16_10490_25317.osm
@app.route("/api/sfbuildingheight_<int:z>_<int:x>_<int:y>.osm")
def changeset(z,x,y):
  if z < 16:
    print "Too big"
    raise Exception
  bb = mercantile.bounds(x,y,z)
  bb = [str(f) for f in [bb.west,bb.south,bb.east,bb.north]]
  url = "http://openstreetmap.org/api/0.6/map?bbox=" + ','.join(bb)
  osm_api_response = requests.get(url)
  changeset = task.changeset(BytesIO(osm_api_response.content),height_db)

  filename = "sfbuildingheight_{0}_{1}_{2}.osm".format(z,x,y)
  return Response(etree.tostring(changeset,pretty_print=True),
    mimetype="text/xml",
    headers={
    'Content-Disposition':'attachment; filename={0}'.format(filename)
  })

if __name__ == "__main__":
  app.debug = True
  app.run()
