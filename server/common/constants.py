## Constants wooo

#Formats for exported files
TABLE_FILE_FORMATS = ( 'xls', 'csv' )

#Stats
SIT_STAT = 'site_STAT' #Site
OWN_STAT = 'owner_STAT' #Owner
DTE_STAT = 'str_date_STAT' #Date

REQ_STAT = 'request_count_STAT' #Request count
IMP_STAT = 'impression_count_STAT' #Impression count
CLK_STAT = 'click_count_STAT' #Click count
UU_STAT  = 'unique_user_count_STAT'  #Unique user count

REV_STAT = 'revenue_STAT' #Revenue
CNV_STAT = 'conversion_count_STAT' #Conversion count

FLR_STAT = 'fill_rate_p_STAT' #Fill Rate
CPA_STAT = 'cpa_p_STAT' #CPA
CTR_STAT = 'ctr_p_STAT' #CTR
CNV_RATE_STAT = 'conv_rate_p_STAT' #Conversion rate
CPM_STAT = 'cpm_p_STAT' #CPM
CPC_STAT = 'cpc_p_STAT' #CPC


ALL_STATS =   ( SIT_STAT,
                OWN_STAT,
                DTE_STAT,

                REQ_STAT,
                IMP_STAT,
                CLK_STAT,
                UU_STAT,
                REV_STAT,
                CNV_STAT,

                FLR_STAT,
                CPA_STAT,
                CTR_STAT,
                CNV_RATE_STAT,
                CPM_STAT,
                CPC_STAT,
                )

#I don't have special characters because this is going into a regex and I'm lazy
MARKET_SEARCH_KEY = "klfaa3dadfkfl28903uagnOMGSOSECRETkd938lvkjval8f285had9a834"
MARKET_URL = "https://market.android.com/search?q=%s&c=apps"

CITY_GEO = "city_name=%s,region_name=%s,country_name=%s"
REGION_GEO = "region_name=%s,country_name=%s"
COUNTRY_GEO = "country_name=%s"

########################
# Formatting Constants
########################

# A valid "format" is one of the accepted entries for format in the site model (I think it's the site model...)

#Valid ad "formats" for smartphone adunits that are set to "full"
VALID_FULL_FORMATS = ('300x250', 'full', 'full_landscape',)
#Valid ad "formats" for tablet adunits that are set to "full"
VALID_TABLET_FULL_FORMATS = ('300x250','160x600', 'full_tablet', 'full_tablet_landscape',)

#Networks that can serve fullsize ads
FULL_NETWORKS = ('brightroll',)

# End formatting constants

#Name Mapper for countries with more than 1 country code (Dammit UK why are you now GB??!!?)
ACCEPTED_MULTI_COUNTRY = {'GB' : ['UK', 'GB'],
                          'UK' : ['UK', 'GB'],
                          }
