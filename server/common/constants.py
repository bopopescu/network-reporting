## Global Constants

# True for production, False for not production
IS_PROD = True

# OS Versions



IOS_VERSION_CHOICES = (
    ('999','No Max'),
    ('2.0','2.0'),
    ('2.1','2.1'),
    ('3.0','3.0'),
    ('3.1','3.1'),
    ('3.2','3.2'),
    ('4.0','4.0'),
    ('4.1','4.1'),
    ('4.2','4.2'),
    ('4.3','4.3'),
    ('5.0','5.0'),
  )

ANDROID_VERSION_CHOICES = (
    ('999','No Max'),
    ('1.5','1.5'),
    ('1.6','1.6'),
    ('2.0','2.0'),
    ('2.1','2.1'),
    ('2.2','2.2'),
    ('2.3','2.3'),
    ('3.0','3.0'),
  )

MIN_ANDROID_VERSION = '1.5'
MAX_ANDROID_VERSION = '999'
MIN_IOS_VERSION = '2.0'
MAX_IOS_VERSION = '999'


# ISO stuff

ISO_COUNTRIES = (("US","United States"),("AF", "Afghanistan"),("AX", "Aland Islands"),("AL", "Albania"),("DZ", "Algeria"),("AS", "American Samoa"),("AD", "Andorra"),("AO", "Angola"),("AI", "Anguilla"),("AQ", "Antarctica"),("AG", "Antigua and Barbuda"),("AR", "Argentina"),("AM", "Armenia"),("AW", "Aruba"),("AU", "Australia"),("AT", "Austria"),("AZ", "Azerbaijan"),("BS", "Bahamas"),("BH", "Bahrain"),("BD", "Bangladesh"),("BB", "Barbados"),("BY", "Belarus"),("BE", "Belgium"),("BZ", "Belize"),("BJ", "Benin"),("BM", "Bermuda"),("BT", "Bhutan"),("BO", "Bolivia, Plurinational State of"),("BQ", "Bonaire, Saint Eustatius and Saba"),("BA", "Bosnia and Herzegovina"),("BW", "Botswana"),("BV", "Bouvet Island"),("BR", "Brazil"),("IO", "British Indian Ocean Territory"),("BN", "Brunei Darussalam"),("BG", "Bulgaria"),("BF", "Burkina Faso"),("BI", "Burundi"),("KH", "Cambodia"),("CM", "Cameroon"),("CA", "Canada"),("CV", "Cape Verde"),("KY", "Cayman Islands"),("CF", "Central African Republic"),("TD", "Chad"),("CL", "Chile"),("CN", "China"),("CX", "Christmas Island"),("CC", "Cocos (Keeling) Islands"),("CO", "Colombia"),("KM", "Comoros"),("CG", "Congo"),("CD", "Congo, The Democratic Republic of the"),("CK", "Cook Islands"),("CR", "Costa Rica"),("CI", "Cote D'ivoire"),("HR", "Croatia"),("CU", "Cuba"),("CW", "Curacao"),("CY", "Cyprus"),("CZ", "Czech Republic"),("DK", "Denmark"),("DJ", "Djibouti"),("DM", "Dominica"),("DO", "Dominican Republic"),("EC", "Ecuador"),("EG", "Egypt"),("SV", "El Salvador"),("GQ", "Equatorial Guinea"),("ER", "Eritrea"),("EE", "Estonia"),("ET", "Ethiopia"),("FK", "Falkland Islands (Malvinas)"),("FO", "Faroe Islands"),("FJ", "Fiji"),("FI", "Finland"),("FR", "France"),("GF", "French Guiana"),("PF", "French Polynesia"),("TF", "French Southern Territories"),("GA", "Gabon"),("GM", "Gambia"),("GE", "Georgia"),("DE", "Germany"),("GH", "Ghana"),("GI", "Gibraltar"),("GR", "Greece"),("GL", "Greenland"),("GD", "Grenada"),("GP", "Guadeloupe"),("GU", "Guam"),("GT", "Guatemala"),("GG", "Guernsey"),("GN", "Guinea"),("GW", "Guinea-Bissau"),("GY", "Guyana"),("HT", "Haiti"),("HM", "Heard Island and McDonald Islands"),("VA", "Holy See (Vatican City State)"),("HN", "Honduras"),("HK", "Hong Kong"),("HU", "Hungary"),("IS", "Iceland"),("IN", "India"),("ID", "Indonesia"),("IR", "Iran, Islamic Republic of"),("IQ", "Iraq"),("IE", "Ireland"),("IM", "Isle of Man"),("IL", "Israel"),("IT", "Italy"),("JM", "Jamaica"),("JP", "Japan"),("JE", "Jersey"),("JO", "Jordan"),("KZ", "Kazakhstan"),("KE", "Kenya"),("KI", "Kiribati"),("KP", "Korea, Democratic People's Republic of"),("KR", "Korea, Republic of"),("KW", "Kuwait"),("KG", "Kyrgyzstan"),("LA", "Lao People's Democratic Republic"),("LV", "Latvia"),("LB", "Lebanon"),("LS", "Lesotho"),("LR", "Liberia"),("LY", "Libyan Arab Jamahiriya"),("LI", "Liechtenstein"),("LT", "Lithuania"),("LU", "Luxembourg"),("MO", "Macao"),("MK", "Macedonia, The Former Yugoslav Republic of"),("MG", "Madagascar"),("MW", "Malawi"),("MY", "Malaysia"),("MV", "Maldives"),("ML", "Mali"),("MT", "Malta"),("MH", "Marshall Islands"),("MQ", "Martinique"),("MR", "Mauritania"),("MU", "Mauritius"),("YT", "Mayotte"),("MX", "Mexico"),("FM", "Micronesia, Federated States of"),("MD", "Moldova, Republic of"),("MC", "Monaco"),("MN", "Mongolia"),("ME", "Montenegro"),("MS", "Montserrat"),("MA", "Morocco"),("MZ", "Mozambique"),("MM", "Myanmar"),("NA", "Namibia"),("NR", "Nauru"),("NP", "Nepal"),("NL", "Netherlands"),("NC", "New Caledonia"),("NZ", "New Zealand"),("NI", "Nicaragua"),("NE", "Niger"),("NG", "Nigeria"),("NU", "Niue"),("NF", "Norfolk Island"),("MP", "Northern Mariana Islands"),("NO", "Norway"),("OM", "Oman"),("PK", "Pakistan"),("PW", "Palau"),("PS", "Palestinian Territory, Occupied"),("PA", "Panama"),("PG", "Papua New Guinea"),("PY", "Paraguay"),("PE", "Peru"),("PH", "Philippines"),("PN", "Pitcairn"),("PL", "Poland"),("PT", "Portugal"),("PR", "Puerto Rico"),("QA", "Qatar"),("RE", "Reunion"),("RO", "Romania"),("RU", "Russian Federation"),("RW", "Rwanda"),("BL", "Saint Barthelemy"),("SH", "Saint Helena, Ascension and Tristan Da Cunha"),("KN", "Saint Kitts and Nevis"),("LC", "Saint Lucia"),("MF", "Saint Martin (French Part)"),("PM", "Saint Pierre and Miquelon"),("VC", "Saint Vincent and the Grenadines"),("WS", "Samoa"),("SM", "San Marino"),("ST", "Sao Tome and Principe"),("SA", "Saudi Arabia"),("SN", "Senegal"),("RS", "Serbia"),("SC", "Seychelles"),("SL", "Sierra Leone"),("SG", "Singapore"),("SX", "Sint Maarten (Dutch Part)"),("SK", "Slovakia"),("SI", "Slovenia"),("SB", "Solomon Islands"),("SO", "Somalia"),("ZA", "South Africa"),("GS", "South Georgia and the South Sandwich Islands"),("ES", "Spain"),("LK", "Sri Lanka"),("SD", "Sudan"),("SR", "Suriname"),("SJ", "Svalbard and Jan Mayen"),("SZ", "Swaziland"),("SE", "Sweden"),("CH", "Switzerland"),("SY", "Syrian Arab Republic"),("TW", "Taiwan, Province of China"),("TJ", "Tajikistan"),("TZ", "Tanzania, United Republic of"),("TH", "Thailand"),("TL", "Timor-Leste"),("TG", "Togo"),("TK", "Tokelau"),("TO", "Tonga"),("TT", "Trinidad and Tobago"),("TN", "Tunisia"),("TR", "Turkey"),("TM", "Turkmenistan"),("TC", "Turks and Caicos Islands"),("TV", "Tuvalu"),("UG", "Uganda"),("UA", "Ukraine"),("AE", "United Arab Emirates"),("GB", "United Kingdom"),("UM", "United States Minor Outlying Islands"),("UY", "Uruguay"),("UZ", "Uzbekistan"),("VU", "Vanuatu"),("VE", "Venezuela, Bolivarian Republic of"),("VN", "Viet Nam"),("VG", "Virgin Islands, British"),("VI", "Virgin Islands, U.S."),("WF", "Wallis and Futuna"),("EH", "Western Sahara"),("YE", "Yemen"),("ZM", "Zambia"),("ZW", "Zimbabwe"),)
US_STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

#Formats for exported files
TABLE_FILE_FORMATS = ( 'xls', 'csv' )

#Stats
SIT_STAT = 'site_STAT' #Site
OWN_STAT = 'owner_STAT' #Owner
DTE_STAT = 'only_date_STAT' #Date

REQ_STAT = 'request_count_STAT' #Request count
IMP_STAT = 'impression_count_STAT' #Impression count
CLK_STAT = 'click_count_STAT' #Click count
UU_STAT  = 'user_count_STAT'  #Unique user count
RU_STAT  = 'request_user_count_STAT'
IU_STAT  = 'impression_user_count_STAT'
CU_STAT  = 'click_user_count_STAT'

REV_STAT = 'revenue_STAT' #Revenue
CNV_STAT = 'conversion_count_STAT' #Conversion count

FLR_STAT = 'fill_rate_STAT' #Fill Rate
CPA_STAT = 'cpa_STAT' #CPA
CTR_STAT = 'ctr_STAT' #CTR
CNV_RATE_STAT = 'conv_rate_STAT' #Conversion rate
CPM_STAT = 'cpm_STAT' #CPM
CPC_STAT = 'cpc_STAT' #CPC


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

APP = 'app'
AU = 'adunit'
CAMP = 'campaign'
CRTV = 'creative'
P = 'priority'
MO = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'
CO = 'country'
MAR = 'marketing'
BRND = 'brand'
OS = 'os'
OS_VER = 'os_ver'
KEY = 'kw'
#I don't have special characters because this is going into a regex and I'm lazy
MARKET_SEARCH_KEY = "klfaa3dadfkfl28903uagnOMGSOSECRETkd938lvkjval8f285had9a834"
#whoooppssss https w/ no login
MARKET_URL = "http://market.android.com/search?q=%s&c=apps"

CITY_GEO = "city_name=%s,region_name=%s,country_name=%s"
REGION_GEO = "region_name=%s,country_name=%s"
COUNTRY_GEO = "country_name=%s"

########################
# Formatting Constants
########################

# A valid "format" is one of the accepted entries for format in the site model (I think it's the site model...)

#Valid ad "formats" for smartphone adunits that are set to "full"
VALID_FULL_FORMATS = ('300x250', 'full', 'full_landscape')
#Valid ad "formats" for tablet adunits that are set to "full"
VALID_TABLET_FULL_FORMATS = ('full_tablet', 'full_tablet_landscape')

#Networks that can serve fullsize ads
FULL_NETWORKS = ('brightroll',)

# End formatting constants

#Name Mapper for countries with more than 1 country code (Dammit UK why are you now GB??!!?)
ACCEPTED_MULTI_COUNTRY = {'GB' : ['UK', 'GB'],
                          'UK' : ['UK', 'GB'],
                          }

CAMPAIGN_LEVELS = ('gtee_high', 'gtee', 'gtee_low', 'promo', 'marketplace', 'network', 'backfill_promo', 'backfill_marketplace')

DATE_FMT = '%y%m%d'

#DATA SIZES
KB = 1024
MB = 1048576
GB = 1073741824
TB = 2**40
PB = 2**50

PIPE_KEY = 'pipeline--%(type)s--%(key)s'
#NOT SCHEDULED REPORT
REP_KEY = 'report:%(d1)s:%(d2)s:%(d3)s:%(account)s:%(start)s:%(end)s'
CLONE_REP_KEY = 'report:%(d1)s:%(d2)s:%(d3)s:%(account)s:%(start)s:%(end)s:%(clone_count)s'

MAX_OBJECTS = 400


MPX_DSP_IDS = [
    '4e45baaddadbc70de9000002', # AdSymptotic
    #'4e8d03fb71729f4a1d000000', # MdotM
    #'4e4d8fb01e368b22f0000000', # TapEngage
    #'4e821f9cab8c762bc4000000', # Qriously
    #'4e8ca48955e9df59fa000000', # mopub_noop
    #'4e69334aa8fd3a790d000000', # TapSense
    # '4e45baaddadbc70de9000001', # TapAd
]

REPORTING_NETWORKS = {'admob': 'AdMob',
                    'jumptap': 'JumpTap',
                    'iad': 'iAd',
                    'inmobi': 'InMobi',
                    'mobfox': 'MobFox'}

NETWORKS_WITHOUT_REPORTING = {'mobfox': 'MobFox',
                              'millennial': 'Millennial',
                              'ejam': 'eJam',
                              'chartboost': 'ChartBoost',
                              'appnexus': 'AppNexus',
                              'brightroll': 'BrightRoll',
                              'greystripe': 'Greystripe'}

NETWORKS = dict(NETWORKS_WITHOUT_REPORTING.items() +
        REPORTING_NETWORKS.items())

