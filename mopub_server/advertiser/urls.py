# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('advertiser.views',
  url(r'^campaign/create/$','campaign_create',name='advertiser_campaign_create'),
  url(r'^campaign/edit/$','campaign_edit',name='advertiser_campaign_edit'),
  url(r'^campaign/delete/$','campaign_delete',name='advertiser_campaign_delete'),
  url(r'^campaign/pause/$','campaign_pause',name='advertiser_campaign_pause'),
  url(r'^campaign/show/(?P<campaign_id>[-\w\.]+)/$','campaign_show',name='advertiser_campaign_show'),
  url(r'^campaign/creative/create/$','creative_create',name='advertiser_creative_create'),
  # url(r'^campaign/creative/edit/$','creative_edit',name='advertiser_creative_edit'),
  url(r'^campaign/creative/delete/$','creative_delete',name='advertiser_creative_delete'),
  # url(r'^campaign/creative/pause/$','creative_pause',name='advertiser_creative_pause'),
  url(r'^campaign/creative/image/(?P<creative_id>[-\w\.]+)/$','creative_image',name='advertiser_creative_image'),
  url(r'^campaign/bid/create/$','bid_create',name='advertiser_bid_create'),
  # url(r'^campaign/bid/edit/$','bid_edit',name='advertiser_bid_edit'),  
  url(r'^campaign/bid/delete/$','bid_delete',name='advertiser_bid_delete'),
  url(r'^campaign/bid/pause/$','bid_pause',name='advertiser_bid_pause'),
  url(r'^campaign/adgroup/edit/$','campaign_adgroup_edit',name='advertiser_campaign_adgroup_edit'),  
  url(r'^campaign/adgroup/(?P<adgroup_id>[-\w\.]+)/$','campaign_adgroup_show',name='advertiser_campaign_adgroup_show'),  
  url(r'^campaign/$','index',name='advertiser_campaigns'),
)