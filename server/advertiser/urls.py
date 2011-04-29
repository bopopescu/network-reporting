# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('advertiser.views',
  url(r'^create/$','campaign_adgroup_create',name='advertiser_campaign_create'),
  url(r'^edit/(?P<adgroup_key>[-\w\.]+)/$','campaign_adgroup_create',name='advertiser_campaign_edit'),
  url(r'^create/ajax/$','campaign_adgroup_create_ajax',name='advertiser_campaign_create_ajax'),
  url(r'^pause/$','campaign_pause',name='advertiser_campaign_pause'),
  url(r'^creative/create/$','creative_create',name='advertiser_creative_create'),
  url(r'^creative/manage/$','creative_manage',name='advertiser_creative_manage'),
  url(r'^creative/image/(?P<creative_key>[-\w\.]+)$','creative_image',name='advertiser_creative_image'),
  url(r'^creative/html/(?P<creative_key>[-\w\.]+)$','creative_html',name='advertiser_creative_html'),
  url(r'^bid/pause/$','bid_pause',name='advertiser_bid_pause'),
  url(r'^adgroup/new/(?P<campaign_key>[-\w\.]+)/$', 'campaign_adgroup_new', name='advertiser_adgroup_new'),
  url(r'^adgroup/edit/(?P<adgroup_key>[-\w\.]+)/$', 'campaign_adgroup_edit', name='advertiser_adgroup_edit'),
  url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/$','campaign_adgroup_show',name='advertiser_adgroup_show'),  
  url(r'^adserver_test/$','adserver_test', name='advertiser_adserver_test'),
  url(r'^$','adgroups',name='advertiser_campaign'),
)
