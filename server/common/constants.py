from adserver_constants import ADSERVER_HOSTNAME

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

COUNTRIES = [
    ('US', "United States"),
    ('AD', "Andorra"),
    ('AE', "United Arab Emirates"),
    ('AF', "Afghanistan"),
    ('AG', "Antigua and Barbuda"),
    ('AI', "Anguilla"),
    ('AL', "Albania"),
    ('AM', "Armenia"),
    ('AO', "Angola"),
    ('AP', "Asia/Pacific Region"),
    ('AQ', "Antarctica"),
    ('AR', "Argentina"),
    ('AS', "American Samoa"),
    ('AT', "Austria"),
    ('AU', "Australia"),
    ('AW', "Aruba"),
    ('AX', "Aland Islands"),
    ('AZ', "Azerbaijan"),
    ('BA', "Bosnia and Herzegovina"),
    ('BB', "Barbados"),
    ('BD', "Bangladesh"),
    ('BE', "Belgium"),
    ('BF', "Burkina Faso"),
    ('BG', "Bulgaria"),
    ('BH', "Bahrain"),
    ('BI', "Burundi"),
    ('BJ', "Benin"),
    ('BL', "Saint Bartelemey"),
    ('BM', "Bermuda"),
    ('BN', "Brunei Darussalam"),
    ('BO', "Bolivia"),
    ('BQ', "Bonaire, Saint Eustatius and Saba"),
    ('BR', "Brazil"),
    ('BS', "Bahamas"),
    ('BT', "Bhutan"),
    ('BV', "Bouvet Island"),
    ('BW', "Botswana"),
    ('BY', "Belarus"),
    ('BZ', "Belize"),
    ('CA', "Canada"),
    ('CC', "Cocos (Keeling) Islands"),
    ('CD', "Congo, The Democratic Republic of the"),
    ('CF', "Central African Republic"),
    ('CG', "Congo"),
    ('CH', "Switzerland"),
    ('CI', "Cote d'Ivoire"),
    ('CK', "Cook Islands"),
    ('CL', "Chile"),
    ('CM', "Cameroon"),
    ('CN', "China"),
    ('CO', "Colombia"),
    ('CR', "Costa Rica"),
    ('CU', "Cuba"),
    ('CV', "Cape Verde"),
    ('CW', "Curacao"),
    ('CX', "Christmas Island"),
    ('CY', "Cyprus"),
    ('CZ', "Czech Republic"),
    ('DE', "Germany"),
    ('DJ', "Djibouti"),
    ('DK', "Denmark"),
    ('DM', "Dominica"),
    ('DO', "Dominican Republic"),
    ('DZ', "Algeria"),
    ('EC', "Ecuador"),
    ('EE', "Estonia"),
    ('EG', "Egypt"),
    ('EH', "Western Sahara"),
    ('ER', "Eritrea"),
    ('ES', "Spain"),
    ('ET', "Ethiopia"),
    ('EU', "Europe"),
    ('FI', "Finland"),
    ('FJ', "Fiji"),
    ('FK', "Falkland Islands (Malvinas)"),
    ('FM', "Micronesia, Federated States of"),
    ('FO', "Faroe Islands"),
    ('FR', "France"),
    ('GA', "Gabon"),
    ('GB', "United Kingdom"),
    ('GD', "Grenada"),
    ('GE', "Georgia"),
    ('GF', "French Guiana"),
    ('GG', "Guernsey"),
    ('GH', "Ghana"),
    ('GI', "Gibraltar"),
    ('GL', "Greenland"),
    ('GM', "Gambia"),
    ('GN', "Guinea"),
    ('GP', "Guadeloupe"),
    ('GQ', "Equatorial Guinea"),
    ('GR', "Greece"),
    ('GS', "South Georgia and the South Sandwich Islands"),
    ('GT', "Guatemala"),
    ('GU', "Guam"),
    ('GW', "Guinea-Bissau"),
    ('GY', "Guyana"),
    ('HK', "Hong Kong"),
    ('HM', "Heard Island and McDonald Islands"),
    ('HN', "Honduras"),
    ('HR', "Croatia"),
    ('HT', "Haiti"),
    ('HU', "Hungary"),
    ('ID', "Indonesia"),
    ('IE', "Ireland"),
    ('IL', "Israel"),
    ('IM', "Isle of Man"),
    ('IN', "India"),
    ('IO', "British Indian Ocean Territory"),
    ('IQ', "Iraq"),
    ('IR', "Iran, Islamic Republic of"),
    ('IS', "Iceland"),
    ('IT', "Italy"),
    ('JE', "Jersey"),
    ('JM', "Jamaica"),
    ('JO', "Jordan"),
    ('JP', "Japan"),
    ('KE', "Kenya"),
    ('KG', "Kyrgyzstan"),
    ('KH', "Cambodia"),
    ('KI', "Kiribati"),
    ('KM', "Comoros"),
    ('KN', "Saint Kitts and Nevis"),
    ('KP', "Korea, Democratic People's Republic of"),
    ('KR', "Korea, Republic of"),
    ('KW', "Kuwait"),
    ('KY', "Cayman Islands"),
    ('KZ', "Kazakhstan"),
    ('LA', "Lao People's Democratic Republic"),
    ('LB', "Lebanon"),
    ('LC', "Saint Lucia"),
    ('LI', "Liechtenstein"),
    ('LK', "Sri Lanka"),
    ('LR', "Liberia"),
    ('LS', "Lesotho"),
    ('LT', "Lithuania"),
    ('LU', "Luxembourg"),
    ('LV', "Latvia"),
    ('LY', "Libyan Arab Jamahiriya"),
    ('MA', "Morocco"),
    ('MC', "Monaco"),
    ('MD', "Moldova, Republic of"),
    ('ME', "Montenegro"),
    ('MF', "Saint Martin"),
    ('MG', "Madagascar"),
    ('MH', "Marshall Islands"),
    ('MK', "Macedonia"),
    ('ML', "Mali"),
    ('MM', "Myanmar"),
    ('MN', "Mongolia"),
    ('MO', "Macao"),
    ('MP', "Northern Mariana Islands"),
    ('MQ', "Martinique"),
    ('MR', "Mauritania"),
    ('MS', "Montserrat"),
    ('MT', "Malta"),
    ('MU', "Mauritius"),
    ('MV', "Maldives"),
    ('MW', "Malawi"),
    ('MX', "Mexico"),
    ('MY', "Malaysia"),
    ('MZ', "Mozambique"),
    ('NA', "Namibia"),
    ('NC', "New Caledonia"),
    ('NE', "Niger"),
    ('NF', "Norfolk Island"),
    ('NG', "Nigeria"),
    ('NI', "Nicaragua"),
    ('NL', "Netherlands"),
    ('NO', "Norway"),
    ('NP', "Nepal"),
    ('NR', "Nauru"),
    ('NU', "Niue"),
    ('NZ', "New Zealand"),
    ('OM', "Oman"),
    ('PA', "Panama"),
    ('PE', "Peru"),
    ('PF', "French Polynesia"),
    ('PG', "Papua New Guinea"),
    ('PH', "Philippines"),
    ('PK', "Pakistan"),
    ('PL', "Poland"),
    ('PM', "Saint Pierre and Miquelon"),
    ('PN', "Pitcairn"),
    ('PR', "Puerto Rico"),
    ('PS', "Palestinian Territory"),
    ('PT', "Portugal"),
    ('PW', "Palau"),
    ('PY', "Paraguay"),
    ('QA', "Qatar"),
    ('RE', "Reunion"),
    ('RO', "Romania"),
    ('RS', "Serbia"),
    ('RU', "Russian Federation"),
    ('RW', "Rwanda"),
    ('SA', "Saudi Arabia"),
    ('SB', "Solomon Islands"),
    ('SC', "Seychelles"),
    ('SD', "Sudan"),
    ('SE', "Sweden"),
    ('SG', "Singapore"),
    ('SH', "Saint Helena"),
    ('SI', "Slovenia"),
    ('SJ', "Svalbard and Jan Mayen"),
    ('SK', "Slovakia"),
    ('SL', "Sierra Leone"),
    ('SM', "San Marino"),
    ('SN', "Senegal"),
    ('SO', "Somalia"),
    ('SR', "Suriname"),
    ('ST', "Sao Tome and Principe"),
    ('SV', "El Salvador"),
    ('SX', "Sint Maarten"),
    ('SY', "Syrian Arab Republic"),
    ('SZ', "Swaziland"),
    ('TC', "Turks and Caicos Islands"),
    ('TD', "Chad"),
    ('TF', "French Southern Territories"),
    ('TG', "Togo"),
    ('TH', "Thailand"),
    ('TJ', "Tajikistan"),
    ('TK', "Tokelau"),
    ('TL', "Timor-Leste"),
    ('TM', "Turkmenistan"),
    ('TN', "Tunisia"),
    ('TO', "Tonga"),
    ('TR', "Turkey"),
    ('TT', "Trinidad and Tobago"),
    ('TV', "Tuvalu"),
    ('TW', "Taiwan"),
    ('TZ', "Tanzania, United Republic of"),
    ('UA', "Ukraine"),
    ('UG', "Uganda"),
    ('UM', "United States Minor Outlying Islands"),
    ('UY', "Uruguay"),
    ('UZ', "Uzbekistan"),
    ('VA', "Holy See (Vatican City State)"),
    ('VC', "Saint Vincent and the Grenadines"),
    ('VE', "Venezuela"),
    ('VG', "Virgin Islands, British"),
    ('VI', "Virgin Islands, U.S."),
    ('VN', "Vietnam"),
    ('VU', "Vanuatu"),
    ('WF', "Wallis and Futuna"),
    ('WS', "Samoa"),
    ('YE', "Yemen"),
    ('YT', "Mayotte"),
    ('ZA', "South Africa"),
    ('ZM', "Zambia"),
    ('ZW', "Zimbabwe"),
]
US_STATES = [
    ("('AR','US')", 'Arkansas'),
    ("('AL','US')", 'Alabama'),
    ("('AK','US')", 'Alaska'),
    ("('AS','US')", 'American Samoa'),
    ("('AZ','US')", 'Arizona'),
    ("('AA','US')", 'Armed Forces Americas'),
    ("('AE','US')", 'Armed Forces Europe, Middle East, & Canada'),
    ("('AP','US')", 'Armed Forces Pacific'),
    ("('CA','US')", 'California'),
    ("('CO','US')", 'Colorado'),
    ("('CT','US')", 'Connecticut'),
    ("('DE','US')", 'Delaware'),
    ("('DC','US')", 'District of Columbia'),
    ("('FM','US')", 'Federated States of Micronesia'),
    ("('FL','US')", 'Florida'),
    ("('GA','US')", 'Georgia'),
    ("('GU','US')", 'Guam'),
    ("('HI','US')", 'Hawaii'),
    ("('ID','US')", 'Idaho'),
    ("('IL','US')", 'Illinois'),
    ("('IN','US')", 'Indiana'),
    ("('IA','US')", 'Iowa'),
    ("('KS','US')", 'Kansas'),
    ("('KY','US')", 'Kentucky'),
    ("('LA','US')", 'Louisiana'),
    ("('ME','US')", 'Maine'),
    ("('MH','US')", 'Marshall Islands'),
    ("('MD','US')", 'Maryland'),
    ("('MA','US')", 'Massachusetts'),
    ("('MI','US')", 'Michigan'),
    ("('MN','US')", 'Minnesota'),
    ("('MS','US')", 'Mississippi'),
    ("('MO','US')", 'Missouri'),
    ("('MT','US')", 'Montana'),
    ("('NE','US')", 'Nebraska'),
    ("('NV','US')", 'Nevada'),
    ("('NH','US')", 'New Hampshire'),
    ("('NJ','US')", 'New Jersey'),
    ("('NM','US')", 'New Mexico'),
    ("('NY','US')", 'New York'),
    ("('NC','US')", 'North Carolina'),
    ("('ND','US')", 'North Dakota'),
    ("('MP','US')", 'Northern Mariana Islands'),
    ("('OH','US')", 'Ohio'),
    ("('OK','US')", 'Oklahoma'),
    ("('OR','US')", 'Oregon'),
    ("('PW','US')", 'Palau'),
    ("('PA','US')", 'Pennsylvania'),
    ("('PR','US')", 'Puerto Rico'),
    ("('RI','US')", 'Rhode Island'),
    ("('SC','US')", 'South Carolina'),
    ("('SD','US')", 'South Dakota'),
    ("('TN','US')", 'Tennessee'),
    ("('TX','US')", 'Texas'),
    ("('UT','US')", 'Utah'),
    ("('VT','US')", 'Vermont'),
    ("('VI','US')", 'Virgin Islands'),
    ("('VA','US')", 'Virginia'),
    ("('WA','US')", 'Washington'),
    ("('WV','US')", 'West Virginia'),
    ("('WI','US')", 'Wisconsin'),
    ("('WY','US')", 'Wyoming'),
]
CA_PROVINCES = [
    ("('AB','CA')", 'Alberta'),
    ("('BC','CA')", 'British Columbia'),
    ("('MB','CA')", 'Manitoba'),
    ("('NB','CA')", 'New Brunswick'),
    ("('NL','CA')", 'Newfoundland'),
    ("('NS','CA')", 'Nova Scotia'),
    ("('NU','CA')", 'Nunavut'),
    ("('ON','CA')", 'Ontario'),
    ("('PE','CA')", 'Prince Edward Island'),
    ("('QC','CA')", 'Quebec'),
    ("('SK','CA')", 'Saskatchewan'),
    ("('NT','CA')", 'Northwest Territories'),
    ("('YT','CA')", 'Yukon Territory'),
]
US_METROS = [
    ("('500','US')", 'Portland-Auburn ME'),
    ("('501','US')", 'New York NY'),
    ("('502','US')", 'Binghamton NY'),
    ("('503','US')", 'Macon GA'),
    ("('504','US')", 'Philadelphia PA'),
    ("('505','US')", 'Detroit MI'),
    ("('506','US')", 'Boston MA-Manchester NH'),
    ("('507','US')", 'Savannah GA'),
    ("('508','US')", 'Pittsburgh PA'),
    ("('509','US')", 'Ft. Wayne IN'),
    ("('510','US')", 'Cleveland-Akron (Canton) OH'),
    ("('511','US')", 'Washington DC (Hagerstown MD)'),
    ("('512','US')", 'Baltimore MD'),
    ("('513','US')", 'Flint-Saginaw-Bay City MI'),
    ("('514','US')", 'Buffalo NY'),
    ("('515','US')", 'Cincinnati OH'),
    ("('516','US')", 'Erie PA'),
    ("('517','US')", 'Charlotte NC'),
    ("('518','US')", 'Greensboro-High Point-Winston Salem NC'),
    ("('519','US')", 'Charleston SC'),
    ("('520','US')", 'Augusta GA'),
    ("('521','US')", 'Providence RI-New Bedford MA'),
    ("('522','US')", 'Columbus GA'),
    ("('523','US')", 'Burlington VT-Plattsburgh NY'),
    ("('524','US')", 'Atlanta GA'),
    ("('525','US')", 'Albany GA'),
    ("('526','US')", 'Utica NY'),
    ("('527','US')", 'Indianapolis IN'),
    ("('528','US')", 'Miami-Ft. Lauderdale FL'),
    ("('529','US')", 'Louisville KY'),
    ("('530','US')", 'Tallahassee FL-Thomasville GA'),
    ("('531','US')", 'Tri-Cities TN-VA'),
    ("('532','US')", 'Albany-Schenectady-Troy NY'),
    ("('533','US')", 'Hartford & New Haven CT'),
    ("('534','US')", 'Orlando-Daytona Beach-Melbourne FL'),
    ("('535','US')", 'Columbus OH'),
    ("('536','US')", 'Youngstown OH'),
    ("('537','US')", 'Bangor ME'),
    ("('538','US')", 'Rochester NY'),
    ("('539','US')", 'Tampa-St. Petersburg (Sarasota) FL'),
    ("('540','US')", 'Traverse City-Cadillac MI'),
    ("('541','US')", 'Lexington KY'),
    ("('542','US')", 'Dayton OH'),
    ("('543','US')", 'Springfield-Holyoke MA'),
    ("('544','US')", 'Norfolk-Portsmouth-Newport News VA'),
    ("('545','US')", 'Greenville-New Bern-Washington NC'),
    ("('546','US')", 'Columbia SC'),
    ("('547','US')", 'Toledo OH'),
    ("('548','US')", 'West Palm Beach-Ft. Pierce FL'),
    ("('549','US')", 'Watertown NY'),
    ("('550','US')", 'Wilmington NC'),
    ("('551','US')", 'Lansing MI'),
    ("('552','US')", 'Presque Isle ME'),
    ("('553','US')", 'Marquette MI'),
    ("('554','US')", 'Wheeling WV-Steubenville OH'),
    ("('555','US')", 'Syracuse NY'),
    ("('556','US')", 'Richmond-Petersburg VA'),
    ("('557','US')", 'Knoxville TN'),
    ("('558','US')", 'Lima OH'),
    ("('559','US')", 'Bluefield-Beckley-Oak Hill WV'),
    ("('560','US')", 'Raleigh-Durham (Fayetteville) NC'),
    ("('561','US')", 'Jacksonville FL'),
    ("('563','US')", 'Grand Rapids-Kalamazoo-Battle Creek MI'),
    ("('564','US')", 'Charleston-Huntington WV'),
    ("('565','US')", 'Elmira NY'),
    ("('566','US')", 'Harrisburg-Lancaster-Lebanon-York PA'),
    ("('567','US')", 'Greenville-Spartanburg SC-Asheville NC-Anderson SC'),
    ("('569','US')", 'Harrisonburg VA'),
    ("('570','US')", 'Florence-Myrtle Beach SC'),
    ("('571','US')", 'Ft. Myers-Naples FL'),
    ("('573','US')", 'Roanoke-Lynchburg VA'),
    ("('574','US')", 'Johnstown-Altoona PA'),
    ("('575','US')", 'Chattanooga TN'),
    ("('576','US')", 'Salisbury MD'),
    ("('577','US')", 'Wilkes Barre-Scranton PA'),
    ("('581','US')", 'Terre Haute IN'),
    ("('582','US')", 'Lafayette IN'),
    ("('583','US')", 'Alpena MI'),
    ("('584','US')", 'Charlottesville VA'),
    ("('588','US')", 'South Bend-Elkhart IN'),
    ("('592','US')", 'Gainesville FL'),
    ("('596','US')", 'Zanesville OH'),
    ("('597','US')", 'Parkersburg WV'),
    ("('598','US')", 'Clarksburg-Weston WV'),
    ("('600','US')", 'Corpus Christi TX'),
    ("('602','US')", 'Chicago IL'),
    ("('603','US')", 'Joplin MO-Pittsburg KS'),
    ("('604','US')", 'Columbia-Jefferson City MO'),
    ("('605','US')", 'Topeka KS'),
    ("('606','US')", 'Dothan AL'),
    ("('609','US')", 'St. Louis MO'),
    ("('610','US')", 'Rockford IL'),
    ("('611','US')", 'Rochester MN-Mason City IA-Austin MN'),
    ("('612','US')", 'Shreveport LA'),
    ("('613','US')", 'Minneapolis-St. Paul MN'),
    ("('616','US')", 'Kansas City MO'),
    ("('617','US')", 'Milwaukee WI'),
    ("('618','US')", 'Houston TX'),
    ("('619','US')", 'Springfield MO'),
    ("('622','US')", 'New Orleans LA'),
    ("('623','US')", 'Dallas-Ft. Worth TX'),
    ("('624','US')", 'Sioux City IA'),
    ("('625','US')", 'Waco-Temple-Bryan TX'),
    ("('626','US')", 'Victoria TX'),
    ("('627','US')", 'Wichita Falls TX & Lawton OK'),
    ("('628','US')", 'Monroe LA-El Dorado AR'),
    ("('630','US')", 'Birmingham AL'),
    ("('631','US')", 'Ottumwa IA-Kirksville MO'),
    ("('632','US')", 'Paducah KY-Cape Girardeau MO-Harrisburg-Mount Vernon IL'),
    ("('633','US')", 'Odessa-Midland TX'),
    ("('634','US')", 'Amarillo TX'),
    ("('635','US')", 'Austin TX'),
    ("('636','US')", 'Harlingen-Weslaco-Brownsville-McAllen TX'),
    ("('637','US')", 'Cedar Rapids-Waterloo-Iowa City & Dubuque IA'),
    ("('638','US')", 'St. Joseph MO'),
    ("('639','US')", 'Jackson TN'),
    ("('640','US')", 'Memphis TN'),
    ("('641','US')", 'San Antonio TX'),
    ("('642','US')", 'Lafayette LA'),
    ("('643','US')", 'Lake Charles LA'),
    ("('644','US')", 'Alexandria LA'),
    ("('647','US')", 'Greenwood-Greenville MS'),
    ("('648','US')", 'Champaign & Springfield-Decatur,IL'),
    ("('649','US')", 'Evansville IN'),
    ("('650','US')", 'Oklahoma City OK'),
    ("('651','US')", 'Lubbock TX'),
    ("('652','US')", 'Omaha NE'),
    ("('656','US')", 'Panama City FL'),
    ("('657','US')", 'Sherman TX-Ada OK'),
    ("('658','US')", 'Green Bay-Appleton WI'),
    ("('659','US')", 'Nashville TN'),
    ("('661','US')", 'San Angelo TX'),
    ("('662','US')", 'Abilene-Sweetwater TX'),
    ("('669','US')", 'Madison WI'),
    ("('670','US')", 'Ft. Smith-Fayetteville-Springdale-Rogers AR'),
    ("('671','US')", 'Tulsa OK'),
    ("('673','US')", 'Columbus-Tupelo-West Point MS'),
    ("('675','US')", 'Peoria-Bloomington IL'),
    ("('676','US')", 'Duluth MN-Superior WI'),
    ("('678','US')", 'Wichita-Hutchinson KS'),
    ("('679','US')", 'Des Moines-Ames IA'),
    ("('682','US')", 'Davenport IA-Rock Island-Moline IL'),
    ("('686','US')", 'Mobile AL-Pensacola (Ft. Walton Beach) FL'),
    ("('687','US')", 'Minot-Bismarck-Dickinson(Williston) ND'),
    ("('691','US')", 'Huntsville-Decatur (Florence) AL'),
    ("('692','US')", 'Beaumont-Port Arthur TX'),
    ("('693','US')", 'Little Rock-Pine Bluff AR'),
    ("('698','US')", 'Montgomery (Selma) AL'),
    ("('702','US')", 'La Crosse-Eau Claire WI'),
    ("('705','US')", 'Wausau-Rhinelander WI'),
    ("('709','US')", 'Tyler-Longview(Lufkin & Nacogdoches) TX'),
    ("('710','US')", 'Hattiesburg-Laurel MS'),
    ("('711','US')", 'Meridian MS'),
    ("('716','US')", 'Baton Rouge LA'),
    ("('717','US')", 'Quincy IL-Hannibal MO-Keokuk IA'),
    ("('718','US')", 'Jackson MS'),
    ("('722','US')", 'Lincoln & Hastings-Kearney NE'),
    ("('724','US')", 'Fargo-Valley City ND'),
    ("('725','US')", 'Sioux Falls(Mitchell) SD'),
    ("('734','US')", 'Jonesboro AR'),
    ("('736','US')", 'Bowling Green KY'),
    ("('737','US')", 'Mankato MN'),
    ("('740','US')", 'North Platte NE'),
    ("('743','US')", 'Anchorage AK'),
    ("('744','US')", 'Honolulu HI'),
    ("('745','US')", 'Fairbanks AK'),
    ("('746','US')", 'Biloxi-Gulfport MS'),
    ("('747','US')", 'Juneau AK'),
    ("('749','US')", 'Laredo TX'),
    ("('751','US')", 'Denver CO'),
    ("('752','US')", 'Colorado Springs-Pueblo CO'),
    ("('753','US')", 'Phoenix AZ'),
    ("('754','US')", 'Butte-Bozeman MT'),
    ("('755','US')", 'Great Falls MT'),
    ("('756','US')", 'Billings MT'),
    ("('757','US')", 'Boise ID'),
    ("('758','US')", 'Idaho Falls-Pocatello ID'),
    ("('759','US')", 'Cheyenne WY-Scottsbluff NE'),
    ("('760','US')", 'Twin Falls ID'),
    ("('762','US')", 'Missoula MT'),
    ("('764','US')", 'Rapid City SD'),
    ("('765','US')", 'El Paso TX'),
    ("('766','US')", 'Helena MT'),
    ("('767','US')", 'Casper-Riverton WY'),
    ("('770','US')", 'Salt Lake City UT'),
    ("('771','US')", 'Yuma AZ-El Centro CA'),
    ("('773','US')", 'Grand Junction-Montrose CO'),
    ("('789','US')", 'Tucson (Sierra Vista) AZ'),
    ("('790','US')", 'Albuquerque-Santa Fe NM'),
    ("('798','US')", 'Glendive MT'),
    ("('800','US')", 'Bakersfield CA'),
    ("('801','US')", 'Eugene OR'),
    ("('802','US')", 'Eureka CA'),
    ("('803','US')", 'Los Angeles CA'),
    ("('804','US')", 'Palm Springs CA'),
    ("('807','US')", 'San Francisco-Oakland-San Jose CA'),
    ("('810','US')", 'Yakima-Pasco-Richland-Kennewick WA'),
    ("('811','US')", 'Reno NV'),
    ("('813','US')", 'Medford-Klamath Falls OR'),
    ("('819','US')", 'Seattle-Tacoma WA'),
    ("('820','US')", 'Portland OR'),
    ("('821','US')", 'Bend OR'),
    ("('825','US')", 'San Diego CA'),
    ("('828','US')", 'Monterey-Salinas CA'),
    ("('839','US')", 'Las Vegas NV'),
    ("('855','US')", 'Santa Barbara-Santa Maria-San Luis Obispo CA'),
    ("('862','US')", 'Sacramento-Stockton-Modesto CA'),
    ("('866','US')", 'Fresno-Visalia CA'),
    ("('868','US')", 'Chico-Redding CA'),
    ("('881','US')", 'Spokane WA'),
]
US_CARRIERS = [
    ('Verizon', 'Verizon'),
    ('AT&T', 'AT&T'),
    ('Sprint', 'Sprint'),
    ('T-Mobile (US)', 'T-Mobile (US)'),
    ('Cellular One', 'Cellular One'),
    ('MetroPCS', 'MetroPCS'),
    ('Cricket', 'Cricket'),
]
GB_CARRIERS = [
    ('British Telecom', 'British Telecom'),
    ('O2', 'O2'),
    ('T-Mobile (GB)', 'T-Mobile (GB)'),
    ('Virgin Mobile (GB)', 'Virgin Mobile (GB)'),
    ('Orange', 'Orange'),
    ('Vectone', 'Vectone'),
    ('TalkTalk', 'TalkTalk'),
]
CA_CARRIERS = [
    ('Telus', 'Telus'),
    ('Fido', 'Fido'),
    ('Bell', 'Bell'),
    ('MTS', 'MTS'),
    ('Virgin Mobile (CA)', 'Virgin Mobile (CA)'),
    ('Rogers', 'Rogers'),
    ('SaskTel', 'SaskTel'),
    ('Videotron', 'Videotron'),
]

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

NETWORKS_WITHOUT_REPORTING = {'millennial': 'Millennial',
                              'adsense': 'AdSense',
                              'ejam': 'TapIt',
                              'brightroll': 'BrightRoll',
                              'custom': 'Custom Network',
                              'custom_native': 'Custom Native Network'}

NETWORKS = dict(NETWORKS_WITHOUT_REPORTING.items() +
        REPORTING_NETWORKS.items())

NETWORK_ADGROUP_TRANSLATION = {'iad': 'iAd',
                               'admob': 'admob_native',
                               'millennial': 'millennial_native'}

PERCENT_DELIVERED_URL = "http://%s/admin/budget/api/delivered" % ADSERVER_HOSTNAME
PACING_URL = "http://%s/admin/budget/api/pacing" % ADSERVER_HOSTNAME
