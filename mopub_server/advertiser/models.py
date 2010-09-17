from appengine_django.models import BaseModel
from google.appengine.ext import db

# Create your models here.
#
# A campaign.  It can run on any number of defined Sites
#	
class Campaign(db.Model):
	name = db.StringProperty()
	description = db.TextProperty()

	budget = db.FloatProperty()		# daily budget in USD
	bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpc")
	
	active = db.BooleanProperty(default=True)
	deleted = db.BooleanProperty(default=False)
	
	# Geographic preferences are expressed as string tuples that can match
	# the city, region or country that is resolved via reverse geocode at 
	# request time.  If the list is blank, any value will match. If the list
	# is not empty, the value must match one of the elements of the list.
	# 
	# Valid predicates are:
	# city_name=X,region_name=X,country_name=X
	# region_name=X,country_name=X
	# country_name=X
	# zipcode=X
	#
	# Each incoming request will be matched against all of these combinations
	geo_predicates = db.StringListProperty(default=["country_name=*"])
	
	# Device and platform preferences are listed similarly:
	#
	# model_name=X,brand_name=X
	# brand_name=X,platform_name=X
	# platform_name=X
	device_predicates = db.StringListProperty(default=["platform_name=*"])
	
	# who owns this
	u = db.UserProperty()	
	t = db.DateTimeProperty(auto_now_add=True)
	
class AdGroup(db.Model):
	campaign = db.ReferenceProperty(Campaign)

	name = db.StringProperty()
	bid = db.FloatProperty()

	active = db.BooleanProperty(default=True)
	deleted = db.BooleanProperty(default=False)

	# all keyword and category bids are tracked here
	# categories use the category:games convention
	# if any of the input keywords match the n-grams here then we 
	# trigger a match
	keywords = db.StringListProperty()

	# all placements that are considered for this ad group
	# this is a list of keys corresponding to Site objects
	site_keys = db.ListProperty(db.Key)

	def __repr__(self):
		return "AdGroup:'%s'" % self.name

IMAGE_PREDICATES = {"300x250": "format=300x250", 
	"320x50": "format=320x50", 
	"300x50": "format=320x50", 
	"728x90": "format=728x90",
	"468x60": "format=468x60"}
class Creative(db.Model):
  ad_group = db.ReferenceProperty(AdGroup)

  active = db.BooleanProperty(default=True)
  deleted = db.BooleanProperty(default=False)

  ad_type = db.StringProperty(choices=["text", "image"], default="text")

  # text ad properties
  headline = db.StringProperty()
  line1 = db.StringProperty()
  line2 = db.StringProperty()

  # image properties
  image = db.BlobProperty()
  image_width = db.IntegerProperty()
  image_height = db.IntegerProperty()

  # destination URLs
  url = db.StringProperty()
  display_url = db.StringProperty()

  # format predicates
  # format=320x50
  # format=*
  format_predicates = db.StringListProperty(default=["format=*"])	

  # time of creation
  t = db.DateTimeProperty(auto_now_add=True)

  @classmethod
  def get_format_predicates_for_image(c, img):
    fp = IMAGE_PREDICATES.get("%dx%d" % (img.width, img.height))
    return [fp] if fp else None

  # calculates the eCPM for this creative, based on 
  # the CPM bid for the ad group or the CPC bid for the ad group and the predicted CTR for this
  # creative
  def e_cpm(self):
    if self.ad_group.campaign.bid_strategy == 'cpc':
      return self.p_ctr() * self.ad_group.bid * 1000
    elif self.ad_group.campaign.bid_strategy == 'cpm':
      return self.ad_group.bid

  # predicts a CTR for this ad.  We use 1% for now.
  # TODO: implement this in a better way
  def p_ctr(self):
    return 0.01

  def __repr__(self):
    return "Creative:'%s'" % self.headline
