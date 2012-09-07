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

ISO_COUNTRIES = (("US","United States"),("AF", "Afghanistan"),("AX", "Aland Islands"),("AL", "Albania"),("DZ", "Algeria"),("AS", "American Samoa"),("AD", "Andorra"),("AO", "Angola"),("AI", "Anguilla"),("AQ", "Antarctica"),("AG", "Antigua and Barbuda"),("AR", "Argentina"),("AM", "Armenia"),("AN", "Netherlands Antilles"),("AW", "Aruba"),("AU", "Australia"),("AT", "Austria"),("AZ", "Azerbaijan"),("BS", "Bahamas"),("BH", "Bahrain"),("BD", "Bangladesh"),("BB", "Barbados"),("BY", "Belarus"),("BE", "Belgium"),("BZ", "Belize"),("BJ", "Benin"),("BM", "Bermuda"),("BT", "Bhutan"),("BO", "Bolivia, Plurinational State of"),("BQ", "Bonaire, Saint Eustatius and Saba"),("BA", "Bosnia and Herzegovina"),("BW", "Botswana"),("BV", "Bouvet Island"),("BR", "Brazil"),("IO", "British Indian Ocean Territory"),("BN", "Brunei Darussalam"),("BG", "Bulgaria"),("BF", "Burkina Faso"),("BI", "Burundi"),("KH", "Cambodia"),("CM", "Cameroon"),("CA", "Canada"),("CV", "Cape Verde"),("KY", "Cayman Islands"),("CF", "Central African Republic"),("TD", "Chad"),("CL", "Chile"),("CN", "China"),("CX", "Christmas Island"),("CC", "Cocos (Keeling) Islands"),("CO", "Colombia"),("KM", "Comoros"),("CG", "Congo"),("CD", "Congo, The Democratic Republic of the"),("CK", "Cook Islands"),("CR", "Costa Rica"),("CI", "Cote D'ivoire"),("HR", "Croatia"),("CU", "Cuba"),("CW", "Curacao"),("CY", "Cyprus"),("CZ", "Czech Republic"),("DK", "Denmark"),("DJ", "Djibouti"),("DM", "Dominica"),("DO", "Dominican Republic"),("EC", "Ecuador"),("EG", "Egypt"),("SV", "El Salvador"),("GQ", "Equatorial Guinea"),("ER", "Eritrea"),("EE", "Estonia"),("ET", "Ethiopia"),("FK", "Falkland Islands (Malvinas)"),("FO", "Faroe Islands"),("FJ", "Fiji"),("FI", "Finland"),("FR", "France"),("GF", "French Guiana"),("PF", "French Polynesia"),("TF", "French Southern Territories"),("GA", "Gabon"),("GM", "Gambia"),("GE", "Georgia"),("DE", "Germany"),("GH", "Ghana"),("GI", "Gibraltar"),("GR", "Greece"),("GL", "Greenland"),("GD", "Grenada"),("GP", "Guadeloupe"),("GU", "Guam"),("GT", "Guatemala"),("GG", "Guernsey"),("GN", "Guinea"),("GW", "Guinea-Bissau"),("GY", "Guyana"),("HT", "Haiti"),("HM", "Heard Island and McDonald Islands"),("VA", "Holy See (Vatican City State)"),("HN", "Honduras"),("HK", "Hong Kong"),("HU", "Hungary"),("IS", "Iceland"),("IN", "India"),("ID", "Indonesia"),("IR", "Iran, Islamic Republic of"),("IQ", "Iraq"),("IE", "Ireland"),("IM", "Isle of Man"),("IL", "Israel"),("IT", "Italy"),("JM", "Jamaica"),("JP", "Japan"),("JE", "Jersey"),("JO", "Jordan"),("KZ", "Kazakhstan"),("KE", "Kenya"),("KI", "Kiribati"),("KP", "Korea, Democratic People's Republic of"),("KR", "Korea, Republic of"),("KW", "Kuwait"),("KG", "Kyrgyzstan"),("LA", "Lao People's Democratic Republic"),("LV", "Latvia"),("LB", "Lebanon"),("LS", "Lesotho"),("LR", "Liberia"),("LY", "Libyan Arab Jamahiriya"),("LI", "Liechtenstein"),("LT", "Lithuania"),("LU", "Luxembourg"),("MO", "Macao"),("MK", "Macedonia, The Former Yugoslav Republic of"),("MG", "Madagascar"),("MW", "Malawi"),("MY", "Malaysia"),("MV", "Maldives"),("ML", "Mali"),("MT", "Malta"),("MH", "Marshall Islands"),("MQ", "Martinique"),("MR", "Mauritania"),("MU", "Mauritius"),("YT", "Mayotte"),("MX", "Mexico"),("FM", "Micronesia, Federated States of"),("MD", "Moldova, Republic of"),("MC", "Monaco"),("MN", "Mongolia"),("ME", "Montenegro"),("MS", "Montserrat"),("MA", "Morocco"),("MZ", "Mozambique"),("MM", "Myanmar"),("NA", "Namibia"),("NR", "Nauru"),("NP", "Nepal"),("NL", "Netherlands"),("NC", "New Caledonia"),("NZ", "New Zealand"),("NI", "Nicaragua"),("NE", "Niger"),("NG", "Nigeria"),("NU", "Niue"),("NF", "Norfolk Island"),("MP", "Northern Mariana Islands"),("NO", "Norway"),("OM", "Oman"),("PK", "Pakistan"),("PW", "Palau"),("PS", "Palestinian Territory, Occupied"),("PA", "Panama"),("PG", "Papua New Guinea"),("PY", "Paraguay"),("PE", "Peru"),("PH", "Philippines"),("PN", "Pitcairn"),("PL", "Poland"),("PT", "Portugal"),("PR", "Puerto Rico"),("QA", "Qatar"),("RE", "Reunion"),("RO", "Romania"),("RU", "Russian Federation"),("RW", "Rwanda"),("BL", "Saint Barthelemy"),("SH", "Saint Helena, Ascension and Tristan Da Cunha"),("KN", "Saint Kitts and Nevis"),("LC", "Saint Lucia"),("MF", "Saint Martin (French Part)"),("PM", "Saint Pierre and Miquelon"),("VC", "Saint Vincent and the Grenadines"),("WS", "Samoa"),("SM", "San Marino"),("ST", "Sao Tome and Principe"),("SA", "Saudi Arabia"),("SN", "Senegal"),("RS", "Serbia"),("SC", "Seychelles"),("SL", "Sierra Leone"),("SG", "Singapore"),("SX", "Sint Maarten (Dutch Part)"),("SK", "Slovakia"),("SI", "Slovenia"),("SB", "Solomon Islands"),("SO", "Somalia"),("ZA", "South Africa"),("GS", "South Georgia and the South Sandwich Islands"),("ES", "Spain"),("LK", "Sri Lanka"),("SD", "Sudan"),("SR", "Suriname"),("SJ", "Svalbard and Jan Mayen"),("SZ", "Swaziland"),("SE", "Sweden"),("CH", "Switzerland"),("SY", "Syrian Arab Republic"),("TW", "Taiwan, Province of China"),("TJ", "Tajikistan"),("TZ", "Tanzania, United Republic of"),("TH", "Thailand"),("TL", "Timor-Leste"),("TG", "Togo"),("TK", "Tokelau"),("TO", "Tonga"),("TT", "Trinidad and Tobago"),("TN", "Tunisia"),("TR", "Turkey"),("TM", "Turkmenistan"),("TC", "Turks and Caicos Islands"),("TV", "Tuvalu"),("UG", "Uganda"),("UA", "Ukraine"),("AE", "United Arab Emirates"),("GB", "United Kingdom"),("UK", "United Kingdom"),("UM", "United States Minor Outlying Islands"),("UY", "Uruguay"),("UZ", "Uzbekistan"),("VU", "Vanuatu"),("VE", "Venezuela, Bolivarian Republic of"),("VN", "Viet Nam"),("VG", "Virgin Islands, British"),("VI", "Virgin Islands, U.S."),("WF", "Wallis and Futuna"),("EH", "Western Sahara"),("YE", "Yemen"),("ZM", "Zambia"),("ZW", "Zimbabwe"),)
US_STATES = [("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("AR","Arkansas"),("CA","California"),("CO","Colorado"),("CT","Connecticut"),("DC","Washington, D.C."),("DE","Deleware"),("FL","Florida"),("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),("IL","Illinois"),("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),("KY","Kentucky"),("LA","Louisiana"),("ME","Maine"),("MD","Maryland"),("MA","Massachusetts"),("MI","Michigan"),("MN","Minnesota"),("MS","Mississippi"),("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),("NV","Nevada"),("NH","New Hampshire"),("NJ","New Jersey"),("NM","New Mexico"),("NY","New York"),("NC","North Carolina"),("ND","North Dakota"),("OH","Ohio"),("OK","Oklahoma"),("OR","Oregon"),("PA","Pennsylvania"),("RI","Rhode Island"),("SC","South Carolina"),("SD","South Dakota"),("TN","Tennessee"),("TX","Texas"),("UT","Utah"),("VT","Vermont"),("VA","Virginia"),("WA","Washington"),("WV","West Virginia"),("WI","Wisconsin"),("WY","Wyoming")]
CA_PROVINCES = [("AB","Alberta"),("BC","British Columbia"),("MB","Manitoba"),("NB","New Brunswick"),("NL","Newfoundland and Labrador"),("NT","Northwest Territories"),("NS","Nova Scotia"),("NU","Nunavut"),("ON","Ontario"),("PE","Prince Edward Island"),("QC","Quebec"),("SK","Saskatchewan"),("YT","Yukon")]
STATES_AND_PROVINCES = [("", "-")] + US_STATES + CA_PROVINCES

#Formats for exported files
TABLE_FILE_FORMATS = ( 'xls', 'csv' )

ISO_COUNTRY_LOOKUP_TABLE = {}
for country_tuple in ISO_COUNTRIES:
    ISO_COUNTRY_LOOKUP_TABLE[country_tuple[0]] = country_tuple[1]
    ISO_COUNTRY_LOOKUP_TABLE[country_tuple[1]] = country_tuple[0]

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


ALL_STATS = (
    SIT_STAT,
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

# Network Configuration
REPORTING_NETWORKS = {
    'admob': 'AdMob',
    'jumptap': 'JumpTap',
    'iad': 'iAd',
    'inmobi': 'InMobi',
    'mobfox': 'MobFox'
}

NETWORKS_WITHOUT_REPORTING = {
    'millennial': 'Millennial',
    'adsense': 'AdSense',
    'ejam': 'TapIt',
    'brightroll': 'BrightRoll',
    'custom': 'Custom Network',
    'custom_native': 'Custom Native Network'
}

NETWORKS = dict(NETWORKS_WITHOUT_REPORTING.items() +
        REPORTING_NETWORKS.items())

NETWORK_ADGROUP_TRANSLATION = {
    'iad': 'iAd',
    'admob': 'admob_native',
    'millennial': 'millennial_native'
}

IAB_CATEGORIES = (
    ('IAB1', 'Arts & Entertainment', (
        ('IAB1-1', 'Books & Literature'),
        ('IAB1-2', 'Celebrity Fan/Gossip'),
        ('IAB1-3', 'Fine Art'),
        ('IAB1-4', 'Humor'),
        ('IAB1-5', 'Movies'),
        ('IAB1-6', 'Music'),
        ('IAB1-7', 'Television'),
    )),
    ('IAB2', 'Automotive', (
        ('IAB2-1', 'Auto Parts'),
        ('IAB2-2', 'Auto Repair'),
        ('IAB2-3', 'Buying/Selling Cars'),
        ('IAB2-4', 'Car Culture'),
        ('IAB2-5', 'Certified Pre-Owned'),
        ('IAB2-6', 'Convertible'),
        ('IAB2-7', 'Coupe'),
        ('IAB2-8', 'CrossoverOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB2-9', 'Diesel'),
        ('IAB2-10', 'Electric Vehicle'),
        ('IAB2-11', 'Hatchback'),
        ('IAB2-12', 'Hybrid'),
        ('IAB2-13', 'Luxury'),
        ('IAB2-14', 'MiniVan'),
        ('IAB2-15', 'Mororcycles'),
        ('IAB2-16', 'Off-Road Vehicles'),
        ('IAB2-17', 'Performance Vehicles'),
        ('IAB2-18', 'Pickup'),
        ('IAB2-19', 'Road-Side Assistance'),
        ('IAB2-20', 'Sedan'),
        ('IAB2-21', 'Trucks & Accessories'),
        ('IAB2-22', 'Vintage Cars'),
        ('IAB2-23', 'Wagon'),
        )),
    ('IAB3', 'Business', (
        ('IAB3-1', 'Advertising'),
        ('IAB3-2', 'Agriculture'),
        ('IAB3-3', 'Biotech/Biomedical'),
        ('IAB3-4', 'Business Software'),
        ('IAB3-5', 'Construction'),
        ('IAB3-6', 'Forestry'),
        ('IAB3-7', 'Government'),
        ('IAB3-8', 'Green Solutions'),
        ('IAB3-9', 'Human Resources'),
        ('IAB3-10', 'Logistics'),
        ('IAB3-11', 'Marketing'),
        ('IAB3-12', 'Metals'),
        )),
    ('IAB4', 'Careers', (
        ('IAB4-1', 'Career Planning'),
        ('IAB4-2', 'College'),
        ('IAB4-3', 'Financial AidOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB4-4', 'Job Fairs'),
        ('IAB4-5', 'Job Search'),
        ('IAB4-6', 'Resume Writing/Advice'),
        ('IAB4-7', 'Nursing'),
        ('IAB4-8', 'Scholarships'),
        ('IAB4-9', 'Telecommuting'),
        ('IAB4-10', 'U.S. Military'),
        ('IAB4-11', 'Career Advice'),
        )),
    ('IAB5', 'Education', (
        ('IAB5-1', '7-12 Education'),
        ('IAB5-2', 'Adult Education'),
        ('IAB5-3', 'Art History'),
        ('IAB5-4', 'Colledge Administration'),
        ('IAB5-5', 'College Life'),
        ('IAB5-6', 'Distance Learning'),
        ('IAB5-7', 'English as a 2nd Language'),
        ('IAB5-8', 'Language Learning'),
        ('IAB5-9', 'Graduate School'),
        ('IAB5-10', 'Homeschooling'),
        ('IAB5-11', 'Homework/Study Tips'),
        ('IAB5-12', 'K-6 Educators'),
        ('IAB5-13', 'Private School'),
        ('IAB5-14', 'Special Education'),
        ('IAB5-15', 'Studying Business'),
        )),
    ('IAB6', 'Family & Parenting', (
        ('IAB6-1', 'Adoption'),
        ('IAB6-2', 'Babies & Toddlers'),
        ('IAB6-3', 'Daycare/Pre School'),
        ('IAB6-4', 'Family Internet'),
        ('IAB6-5', 'Parenting - K-6 Kids'),
        ('IAB6-6', 'Parenting teens'),
        ('IAB6-7', 'PregnancyOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB6-8', 'Special Needs Kids'),
        ('IAB6-9', 'Eldercare'),
        )),
    ('IAB7', 'Health & Fitness', (
        ('IAB7-1', 'Exercise'),
        ('IAB7-2', 'A.D.D.'),
        ('IAB7-3', 'AIDS/HIV'),
        ('IAB7-4', 'Allergies'),
        ('IAB7-5', 'Alternative Medicine'),
        ('IAB7-6', 'Arthritis'),
        ('IAB7-7', 'Asthma'),
        ('IAB7-8', 'Autism/PDD'),
        ('IAB7-9', 'Bipolar Disorder'),
        ('IAB7-10', 'Brain Tumor'),
        ('IAB7-11', 'Cancer'),
        ('IAB7-12', 'Cholesterol'),
        ('IAB7-13', 'Chronic Fatigue Syndrome'),
        ('IAB7-14', 'Chronic Pain'),
        ('IAB7-15', 'Cold & Flu'),
        ('IAB7-16', 'Deafness'),
        ('IAB7-17', 'Dental Care'),
        ('IAB7-18', 'Depression'),
        ('IAB7-19', 'Dermatology'),
        ('IAB7-20', 'Diabetes'),
        ('IAB7-21', 'Epilepsy'),
        ('IAB7-22', 'GERD/Acid Reflux'),
        ('IAB7-23', 'Headaches/Migraines'),
        ('IAB7-24', 'Heart Disease'),
        ('IAB7-25', 'Herbs for Health'),
        ('IAB7-26', 'Holistic Healing'),
        ('IAB7-27', 'IBS/Crohn\'s Disease'),
        ('IAB7-28', 'Incest/Abuse Support'),
        ('IAB7-29', 'IncontinenceOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB7-30', 'Infertility'),
        ('IAB7-31', 'Men\'s Health'),
        ('IAB7-32', 'Nutrition'),
        ('IAB7-33', 'Orthopedics'),
        ('IAB7-34', 'Panic/Anxiety Disorders'),
        ('IAB7-35', 'Pediatrics'),
        ('IAB7-36', 'Physical Therapy'),
        ('IAB7-37', 'Psychology/Psychiatry'),
        ('IAB7-38', 'Senor Health'),
        ('IAB7-39', 'Sexuality'),
        ('IAB7-40', 'Sleep Disorders'),
        ('IAB7-41', 'Smoking Cessation'),
        ('IAB7-42', 'Substance Abuse'),
        ('IAB7-43', 'Thyroid Disease'),
        ('IAB7-44', 'Weight Loss'),
        ('IAB7-45', 'Women\'s Health'),
        )),
    ('IAB8', 'Food & Drink', (
        ('IAB8-1', 'American Cuisine'),
        ('IAB8-2', 'Barbecues & Grilling'),
        ('IAB8-3', 'Cajun/Creole'),
        ('IAB8-4', 'Chinese Cuisine'),
        ('IAB8-5', 'Cocktails/Beer'),
        ('IAB8-6', 'Coffee/Tea'),
        ('IAB8-7', 'Cuisine-Specific'),
        ('IAB8-8', 'Desserts & Baking'),
        ('IAB8-9', 'Dining Out'),
        ('IAB8-10', 'Food Allergies'),
        ('IAB8-11', 'French Cuisine'),
        ('IAB8-12', 'Health/Lowfat Cooking'),
        ('IAB8-13', 'Italian Cuisine'),
        ('IAB8-14', 'Japanese Cuisine'),
        ('IAB8-15', 'Mexican CuisineOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB8-16', 'Vegan'),
        ('IAB8-17', 'Vegetarian'),
        ('IAB8-18', 'Wine'),
        )),
    ('IAB9', 'Hobbies & Interests', (
        ('IAB9-1', 'Art/Technology'),
        ('IAB9-2', 'Arts & Crafts'),
        ('IAB9-3', 'Beadwork'),
        ('IAB9-4', 'Birdwatching'),
        ('IAB9-5', 'Board Games/Puzzles'),
        ('IAB9-6', 'Candle & Soap Making'),
        ('IAB9-7', 'Card Games'),
        ('IAB9-8', 'Chess'),
        ('IAB9-9', 'Cigars'),
        ('IAB9-10', 'Collecting'),
        ('IAB9-11', 'Comic Books'),
        ('IAB9-12', 'Drawing/Sketching'),
        ('IAB9-13', 'Freelance Writing'),
        ('IAB9-14', 'Genealogy'),
        ('IAB9-15', 'Getting Published'),
        ('IAB9-16', 'Guitar'),
        ('IAB9-17', 'Home Recording'),
        ('IAB9-18', 'Investors & Patents'),
        ('IAB9-19', 'Jewelry Making'),
        ('IAB9-20', 'Magic & Illusion'),
        ('IAB9-21', 'Needlework'),
        ('IAB9-22', 'Painting'),
        ('IAB9-23', 'Photography'),
        ('IAB9-24', 'Radio'),
        ('IAB9-25', 'Roleplaying Games'),
        ('IAB9-26', 'Sci-Fi & Fantasy'),
        ('IAB9-27', 'Scrapbooking'),
        ('IAB9-28', 'ScreenwritingOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB9-29', 'Stamps & Coins'),
        ('IAB9-30', 'Video & Computer Games'),
        ('IAB9-31', 'Woodworking'),
        )),
    ('IAB10', 'Home & Garden', (
        ('IAB10-1', 'Appliances'),
        ('IAB10-2', 'Entertaining'),
        ('IAB10-3', 'Environmental Safety'),
        ('IAB10-4', 'Gardening'),
        ('IAB10-5', 'Home Repair'),
        ('IAB10-6', 'Home Theater'),
        ('IAB10-7', 'Interior Decorating'),
        ('IAB10-8', 'Landscaping'),
        ('IAB10-9', 'Remodeling & Construction'),
        )),
    ('IAB11', 'Law, Gov\'t & Politics', (
        ('IAB11-1', 'Immigration'),
        ('IAB11-2', 'Legal Issues'),
        ('IAB11-3', 'U.S. Government Resources'),
        ('IAB11-4', 'Politics'),
        ('IAB11-5', 'Commentary'),
        )),
    ('IAB12', 'News', (
        ('IAB12-1', 'International News'),
        ('IAB12-2', 'National News'),
        ('IAB12-3', 'Local News'),
        )),
    ('IAB13', 'Personal Finance', (
        ('IAB13-1', 'Beginning Investing'),
        ('IAB13-2', 'Credit/Debt & Loans'),
        ('IAB13-3', 'Financial News'),
        ('IAB13-4', 'Financial Planning'),
        ('IAB13-5', 'Hedge Fund'),
        ('IAB13-6', 'Insurance'),
        ('IAB13-7', 'Investing'),
        ('IAB13-8', 'Mutual FundsOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB13-9', 'Options'),
        ('IAB13-10', 'Retirement Planning'),
        ('IAB13-11', 'Stocks'),
        ('IAB13-12', 'Tax Planning'),
        )),
    ('IAB14', 'Society', (
        ('IAB14-1', 'Dating'),
        ('IAB14-2', 'Divorce Support'),
        ('IAB14-3', 'Gay Life'),
        ('IAB14-4', 'Marriage'),
        ('IAB14-5', 'Senior Living'),
        ('IAB14-6', 'Teens'),
        ('IAB14-7', 'Weddings'),
        ('IAB14-8', 'Ethnic Specific'),
        )),
    ('IAB15', 'Science', (
        ('IAB15-1', 'Astrology'),
        ('IAB15-2', 'Biology'),
        ('IAB15-3', 'Chemistry'),
        ('IAB15-4', 'Geology'),
        ('IAB15-5', 'Paranormal Phenomena'),
        ('IAB15-6', 'Physics'),
        ('IAB15-7', 'Space/Astronomy'),
        ('IAB15-8', 'Geography'),
        ('IAB15-9', 'Botany'),
        ('IAB15-10', 'Weather'),
        )),
    ('IAB16', 'Pets', (
        ('IAB16-1', 'Aquariums'),
        ('IAB16-2', 'Birds'),
        ('IAB16-3', 'Cats'),
        ('IAB16-4', 'Dogs'),
        ('IAB16-5', 'Large Animals'),
        ('IAB16-6', 'Reptiles'),
        ('IAB16-7', 'Veterinary MedicineOPENRTB API Specification Version 2.0 RTB Project'),
        )),
    ('IAB17', 'Sports', (
        ('IAB17-1', 'Auto Racing'),
        ('IAB17-2', 'Baseball'),
        ('IAB17-3', 'Bicycling'),
        ('IAB17-4', 'Bodybuilding'),
        ('IAB17-5', 'Boxing'),
        ('IAB17-6', 'Canoeing/Kayaking'),
        ('IAB17-7', 'Cheerleading'),
        ('IAB17-8', 'Climbing'),
        ('IAB17-9', 'Cricket'),
        ('IAB17-10', 'Figure Skating'),
        ('IAB17-11', 'Fly Fishing'),
        ('IAB17-12', 'Football'),
        ('IAB17-13', 'Freshwater Fishing'),
        ('IAB17-14', 'Game & Fish'),
        ('IAB17-15', 'Golf'),
        ('IAB17-16', 'Horse Racing'),
        ('IAB17-17', 'Horses'),
        ('IAB17-18', 'Hunting/Shooting'),
        ('IAB17-19', 'Inline Skating'),
        ('IAB17-20', 'Martial Arts'),
        ('IAB17-21', 'Mountain Biking'),
        ('IAB17-22', 'NASCAR Racing'),
        ('IAB17-23', 'Olympics'),
        ('IAB17-24', 'Paintball'),
        ('IAB17-25', 'Power & Motorcycles'),
        ('IAB17-26', 'Pro Basketball'),
        ('IAB17-27', 'Pro Ice Hockey'),
        ('IAB17-28', 'Rodeo'),
        ('IAB17-29', 'Rugby'),
        ('IAB17-30', 'Running/Jogging'),
        ('IAB17-31', 'SailingOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB17-32', 'Saltwater Fishing'),
        ('IAB17-33', 'Scuba Diving'),
        ('IAB17-34', 'Skateboarding'),
        ('IAB17-35', 'Skiing'),
        ('IAB17-36', 'Snowboarding'),
        ('IAB17-37', 'Surfing/Bodyboarding'),
        ('IAB17-38', 'Swimming'),
        ('IAB17-39', 'Table Tennis/Ping-Pong'),
        ('IAB17-40', 'Tennis'),
        ('IAB17-41', 'Volleyball'),
        ('IAB17-42', 'Walking'),
        ('IAB17-43', 'Waterski/Wakeboard'),
        ('IAB17-44', 'World Soccer'),
        )),
    ('IAB18', 'Style & Fashion', (
        ('IAB18-1', 'Beauty'),
        ('IAB18-2', 'Body Art'),
        ('IAB18-3', 'Fashion'),
        ('IAB18-4', 'Jewelry'),
        ('IAB18-5', 'Clothing'),
        ('IAB18-6', 'Accessories'),
        )),
    ('IAB19', 'Technology & Computing', (
        ('IAB19-1', '3-D Graphics'),
        ('IAB19-2', 'Animation'),
        ('IAB19-3', 'Antivirus Software'),
        ('IAB19-4', 'C/C++'),
        ('IAB19-5', 'Cameras & Camcorders'),
        ('IAB19-6', 'Cell Phones'),
        ('IAB19-7', 'Computer Certification'),
        ('IAB19-8', 'Computer Networking'),
        ('IAB19-9', 'Computer Peripherals'),
        ('IAB19-10', 'Computer Reviews'),
        ('IAB19-11', 'Data CentersOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB19-12', 'Databases'),
        ('IAB19-13', 'Desktop Publishing'),
        ('IAB19-14', 'Desktop Video'),
        ('IAB19-15', 'Email'),
        ('IAB19-16', 'Graphics Software'),
        ('IAB19-17', 'Home Video/DVD'),
        ('IAB19-18', 'Internet Technology'),
        ('IAB19-19', 'Java'),
        ('IAB19-20', 'JavaScript'),
        ('IAB19-21', 'Mac Support'),
        ('IAB19-22', 'MP3/MIDI'),
        ('IAB19-23', 'Net Conferencing'),
        ('IAB19-24', 'Net for Beginners'),
        ('IAB19-25', 'Network Security'),
        ('IAB19-26', 'Palmtops/PDAs'),
        ('IAB19-27', 'PC Support'),
        ('IAB19-28', 'Portable'),
        ('IAB19-29', 'Entertainment'),
        ('IAB19-30', 'Shareware/Freeware'),
        ('IAB19-31', 'Unix'),
        ('IAB19-32', 'Visual Basic'),
        ('IAB19-33', 'Web Clip Art'),
        ('IAB19-34', 'Web Design/HTML'),
        ('IAB19-35', 'Web Search'),
        ('IAB19-36', 'Windows'),
        )),
    ('IAB20', 'Travel', (
        ('IAB20-1', 'Adventure Travel'),
        ('IAB20-2', 'Africa'),
        ('IAB20-3', 'Air Travel'),
        ('IAB20-4', 'Australia & New Zealand'),
        ('IAB20-5', 'Bed & Breakfasts'),
        ('IAB20-6', 'Budget TravelOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB20-7', 'Business Travel'),
        ('IAB20-8', 'By US Locale'),
        ('IAB20-9', 'Camping'),
        ('IAB20-10', 'Canada'),
        ('IAB20-11', 'Caribbean'),
        ('IAB20-12', 'Cruises'),
        ('IAB20-13', 'Eastern Europe'),
        ('IAB20-14', 'Europe'),
        ('IAB20-15', 'France'),
        ('IAB20-16', 'Greece'),
        ('IAB20-17', 'Honeymoons/Getaways'),
        ('IAB20-18', 'Hotels'),
        ('IAB20-19', 'Italy'),
        ('IAB20-20', 'Japan'),
        ('IAB20-21', 'Mexico & Central America'),
        ('IAB20-22', 'National Parks'),
        ('IAB20-23', 'South America'),
        ('IAB20-24', 'Spas'),
        ('IAB20-25', 'Theme Parks'),
        ('IAB20-26', 'Traveling with Kids'),
        ('IAB20-27', 'United Kingdom'),
        )),
    ('IAB21', 'Real Estate', (
        ('IAB21-1', 'Apartments'),
        ('IAB21-2', 'Architects'),
        ('IAB21-3', 'Buying/Selling Homes'),
        )),
    ('IAB22', 'Shopping', (
        ('IAB22-1', 'Contests & Freebies'),
        ('IAB22-2', 'Couponing'),
        ('IAB22-3', 'Comparison'),
        ('IAB22-4', 'Engines'),
        )),
    ('IAB23', 'Religion & Spirituality', (
        ('IAB23-1', 'Alternative ReligionsOPENRTB API Specification Version 2.0 RTB Project'),
        ('IAB23-2', 'Atheism/Agnosticism'),
        ('IAB23-3', 'Buddhism'),
        ('IAB23-4', 'Catholicism'),
        ('IAB23-5', 'Christianity'),
        ('IAB23-6', 'Hinduism'),
        ('IAB23-7', 'Islam'),
        ('IAB23-8', 'Judaism'),
        ('IAB23-9', 'Latter-Day Saints'),
        ('IAB23-10', 'Pagan/Wiccan'),
        )),
    ('IAB24', 'Uncategorized', (
        )),
    ('IAB25', 'Non-Standard Content', (
        ('IAB25-1', 'Unmoderated UGC'),
        ('IAB25-2', 'Extreme Graphic/Explicit Violence'),
        ('IAB25-3', 'Pornography'),
        ('IAB25-4', 'Profane Content'),
        ('IAB25-5', 'Hate Content'),
        ('IAB25-6', 'Under Construction'),
        ('IAB25-7', 'Incentivized'),
        )),
    ('IAB26', 'Illegal Content', (
        ('IAB26-1', 'Illegal Content'),
        ('IAB26-2', 'Warez'),
        ('IAB26-3', 'Spyware/Malware'),
        ('IAB26-4', 'Copyright Infringement'),
    ))
)

CREATIVE_ATTRIBUTES = (
    (1, 'Audio Ad (Auto Play)'),
    (2, 'Audio Ad (User Initiated)'),
    (3, 'Expandable (Automatic)'),
    (4, 'Expandable (User Initiated - Click)'),
    (5, 'Expandable (User Initiated - Rollover)'),
    (6, 'In-Banner Video Ad (Auto Play)'),
    (7, 'In-Banner Video Ad (User Initiated)'),
    (8, 'Pop (e.g., Over, Under, or upon Exit)'),
    (9, 'Provocative or Suggestive Imagery'),
    (10, 'Shaky, Flashing, Flickering, Extreme Animation, Smileys'),
    (11, 'Surveys'),
    (12, 'Text Only'),
    (13, 'User Interactive (e.g., Embedded Games)'),
    (14, 'Windows Dialog or Alert Style'),
    (15, 'Has audio on/off button'),
    (16, 'Ad can be skipped (e.g., skip button on preroll video)')
)

IAB_CATEGORIES_AND_SUBCATEGORIES = set()
for category in IAB_CATEGORIES:
    IAB_CATEGORIES_AND_SUBCATEGORIES.add(category[0])
    for sub_category in category[2]:
        IAB_CATEGORIES_AND_SUBCATEGORIES.add(sub_category[0])

IAB_ATTRIBUTES = set([attribute[0] for attribute in CREATIVE_ATTRIBUTES])