import copy
import os
import sys
import unittest

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from common.utils.helpers import get_url_for_blob
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed
from nose.tools import ok_, eq_

from common.utils.test.fixtures import generate_app, generate_adunit
from common.utils.test.test_utils import model_eq
from publisher.forms import AppForm, AdUnitForm


setup_test_environment()


IMAGE_DATA = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc````\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00\x00\x00IEND\xaeB`\x82'
RESIZED_IMAGE_DATA = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00<\x00\x00\x00<\x08\x06\x00\x00\x00:\xfc\xd9r\x00\x00\x00$IDATx\x9c\xed\xc11\x01\x00\x00\x00\xc2\xa0\xf5O\xedi\t\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00n8|\x00\x01N\x81\x9e\x1b\x00\x00\x00\x00IEND\xaeB`\x82'

DEFAULT_APP_DATA = {
    'name': 'Test App',
    'app_type': 'iphone',
    'primary_category': 'books',
}

DEFAULT_APP_FILES = {
    'img_file': SimpleUploadedFile('icon.png', IMAGE_DATA, content_type='image/png')
}

DEFAULT_IMG_URL = "https://app.mopub.com/images/mopub-logo2.png"
DEFAULT_IMG_URL_DATA = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00x\x00\x00\x003\x08\x06\x00\x00\x00\\\xfb\xcc}\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x03`iTXtXML:com.adobe.xmp\x00\x00\x00\x00\x00<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?> <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.0-c060 61.134777, 2010/02/12-17:32:00        "> <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> <rdf:Description rdf:about="" xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/" xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#" xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmpMM:OriginalDocumentID="uuid:C6A6EFC4EA53DA1197C6BCDC301CBF6F" xmpMM:DocumentID="xmp.did:B59BB4CC153711E090E285B832F927DE" xmpMM:InstanceID="xmp.iid:B59BB4CB153711E090E285B832F927DE" xmp:CreatorTool="Adobe Photoshop CS5 Macintosh"> <xmpMM:DerivedFrom stRef:instanceID="xmp.iid:0280117407206811871FC4C0967E4B45" stRef:documentID="uuid:C6A6EFC4EA53DA1197C6BCDC301CBF6F"/> </rdf:Description> </rdf:RDF> </x:xmpmeta> <?xpacket end="r"?>H\x87\xd2t\x00\x00\x15\x0bIDATx\xda\xec\\\x0bt\x14e\x96\xae\xaa\xae\xeet\x1e\x90\x07Ix\x04\x08 \x10\x10\x0c\x04\x11\x81\x19\x1f3\xcc\xb2\x8a\xe0\x81q<\x8c\xc3:\xea\x8e\x1cqT\xc6=\xb8*\xb8gF\x90Q\xd0\x95UgW=\x82\n\xee\x08\x03\x8b\xec\x9c\xc1\x1d\xdc!<F\x89"\x82\x86\x97\x92\x10\x1e\t$\xe4\xd5yu\xd2\xafz\xfc\xfb\xdd\xa6:VW\xbf\xaa\x1fau\x8euN\x9dNW\xdd\xfa\x1f\xf7\xbb\xf7\xbb\xf7\xfe\xf5wx.\xc1c\xe7\xce\x9d<\xf7\xdda<R\xa5\x13\x16K`\xde\xbcy,\xa5\x03\xfa\x0e\xd0\x84\xf4\xc6\xa7\x00P\x96\x0c\xc8<\x80K\x95E\xf2\xdf\x81\x1e\xf7}\x16\'\xa8\xf1^\xe7\xc4$\xc0\xe2\xfb\x18t\xf6-\xf6\xdeD=\x9c\x85\xb9\xce\x0c\xf2,B;\xcc,\xc0\x89X"\x9f\xa4\x92\xd8\xb7\x94\x11\xf8\x14\x1a7\x8b\x00,\x1f\xe3;\x17\xed\xba\x98\xe4\x80\xf9\x14\x81\xf2m\xa7\xf7d\x8d>\x1c\xb8\xe1\x80\x8d\xdb\x9bE\x13\x03\x8a5x\xfeo\x100\x96\x02Z\xe6\xfb`L\xb1@\x0f\x01Y\x8c\x13\\\xfeo\x1cd\x96\xc4|R\x05\xb0\x11H\xde\xf0\xc9E\xf9;\x04d1Ip\xf9+h\xc1W\x8ajY\x8a\xe2m,}\xb0\x04\x81\x8f\x0bd1Np\xe3\x019^\x85\xb0o\x10\xc8\xe1\xb2\xd7\x84\xbc\xb7\xa3\xa3\x83ojj\xb2466Z\xba\xbb\xbb\x05\x9f\xcf\xc7gee\xa9\xe9\xe9\xe9Jqq\xb1\xd2\xaf_?\x96\x93\x93\xa3\xc6\x00\xd4lR\xca\x12\xc9\xa2y\x93\x9f\xc9\xd26\xff\r\x03\x9bO\xf0~\x90\x0e\xdcn\xb7p\xee\xdc9\xdb\x8b/\xbe\xf8\xa7\xb4\xb4\xb4\x19\x81\x1b\xed\xed\xed\xeb\x9e~\xfa\xe9\xdfN\x9b6\xcd\x87\xaf\x82\xc99G\xa2\xef\x88 \x8b&\'\xc1\xf7\x01\xd8\x89*\x97\xa5\x084\x96b\xd0\xc3\xce\xf7\xd2\xa5K\xe2\x85\x0b\x172$I\xb2\x02\xe0^\x01x\xb3\x1d^\x9d\xd6\xd2\xd2\xa2dgg+ab\xad\x1e\xacp\xc0F\x02\x993[&\x99\x013^\xa0\xaf\xd4BC\xaa\xdaa\t\x84\x9b\xa0\xb9{\xbd^\xb1\xa7\xa7\'\r\x00\x07\xe9\xda\xe3\xf1\xd8p\xdd&\xcb\xb2\x17_\xd5$\xb3\xe8\x88\xf1XL\x00\xdcx\x00\xee\xab\xc4+U\xde\xc7\xe2|\x86\x8f\x93\xf18A\x10xUUEEQ,zA\xc4b\x11\xf7D\x00/\xe8(\x9a\xe7\xcc\xadK\x9b\xce\xb2\xc58\x14\x13\x0e\xdcD\xa8\xfb\xdb\xe6\xc5\xc9\xd4\xbf\xbc\xd5j\x15,\x16K\xd8|\x84\xc0\xa73B\x1bf\x81\x8ej\xa4b\x82\xd9q\x10\xb8]]]\x02\x8f\x03\xf1\x84\xb2D\xb2F.33\x93\xcb\xcb\xcb#\xea\xe1\xf1w\xef\x80\\.\x17%\x1e|gg\xa7\x10h\x101\x88\xb2J\x96\x91\x91\x11\xd33\xe3|>,\xc5R\x1bZ\xa2#\x80B\xc9\xc3\x98\xddng\xb9\xb9\xb9\xaa6v\x96\xa0A\x845\xe8\x08\x00\xfb\xaf\x8b\xa2(\xe8\xf4\xc9\x12d\xb2\x88^,\xc6a\x9d\xbc\x11\\R2@\xb5444X\x1bG\x94\xe6y\xcbn\xbb\x91\xcb\xca\x99H}\xf0>\xcf\x05[]u\xc5\xa8\x93\x1f\x9e\x07\xd0\n\x00\xe0\xc8\x10\xea\xeb\xeb\xc5\xa6\xb9\x8b\xbf\xaf\x94\x16\xcc\xe4\x18\xe39U\xe9\xb4\xb6\xd4W\x0c\xde\xb7\xf5\x18\x95\r\x85\x85\x852\x81\xa5\x1f\x04\x01J\'\xf5\xd5\xfb\xfc\x84\xdc\x89\x9c`\xc9\xe6x\x9eY\xda[>\x1e\xf8\xfe\xfa\x03EEErAA\x01\xf5\xc5\xb46xC;Bss\xb3\xc5\xe1p\x083g\xce\x1c9c\xc6\x8c\xef\x01\xd8a\xda\\N\xd6\xd5\xd5\x1d;p\xe0\x80\x7f\xbc\x03\x07\x0e\xf4\xb7C\xfd\xa2\xd4\x11Z[[-N\xa7\x93G\xcc\xa42\x87\xc1\x08T]_\xfe1"\xae\xf2h[D\x02E\x86,PR\x85\xefV4oe4W\xdd\x01\xa3"\xe3\xb2\xd5\xd4\xd4\xd8\xa9\x8c\xa2vA\xe3\xd4\x96Jm\xe7\xe7\xe7\xcb08\x85J*\x13+l\x113i^{\xcf\x1b+\xe6\x86|\'p\x8f\x1f?n;[:k4\x9bx\xfd\xe3|f\xff;\xc2\x9a\x98\xc7}H\xfc\xf4\x7f\x1f\xcf\xa8\xd8Y\xe7\\\xbc\xea~n\xc0\xe0G\x10\x98\xfa\x85\x08\xcaR\x83\xd0pn\xf5\xa8\xdd\x1bw^u\xd5U\x12y%y\x15)\x8d\x80E\xa9a\xad\xbd\xe3\xd1%,\xa7\xe0^N\xb4\x0e\ty^U\x9d|\xa7cS\xf1\xb6\x17\x9e\x1f9r\xa4D\xca\xa7\xe7\xb5\x84\xc6?^d\xb4\x96y\xf3\xe6\xdd<z\xf4\xe8G\xe1\xed\xd7E`\x88\xcf\x8e\x1d;\xb6r\xf7\xee\xdd\x9f\xa3\x1d\x99\x9e\x05\xf0\xe2SO=\xb5\x03\x80]\x1f\x90kkk{\xe5\xb5\xd7^[;n\xdc8)0\xceS\xa7NY\x1f|\xf0\xc1\'` Ku\xed\x1d\xbe\xed\xb6\xdb\x1e\xda\xbau\xeb[0\xde\t\x81\xeb\x95\x95\x95\x9b1\x9e\x0fo\xbd\xf5\xd6\xd7\r\xc0\xc3\x8e\x9c\xbba\xc8[7o\xde\xbc\x7f\xf0\xe0\xc1\xd2\x80\x01\x03\xa8^V4\xe0"\x9d\\\xb8O!\xce\x95\xac^p\x8f\x1c9\x92vj\xca\xdci\xca\x94Y\xe5\xaa\xbd\xff\x1d\n\xba\x0fw\xaa\xd6\xf4i\xbe\x19\xf3\xdew,y~\xa3\x92W\xb4BaB\xbf\xb0\xb2\xbcu\x88T4\xf6\xd5\xaa\x9f<\xfe\xbb\xd3\xa7O\xa7\xc1\xdb-P\x1a1\x84\xf8\xb9\x9c>\xf0\xcc?\xfcf\x87\x9c;d\x05\xc9\x85}\x1e\xed\xca\xfd\x0b\x1e>\xf3\xf3U\xbb\x8fx\xad\x83\x89U\xe8y:\xa9\xad3g\xce\xd8\xef\xbb\xef\xbe\xa7&L\x98\xf0.\x80\xba\x0e\xde\xc2\x85;\xe9\x1e\x8e\xf7\x17.\\xouu\xb5\x1d\xfd[\xa1\xecLx\xa8U/\x876\xd3\xc0\x06\xfeqja\xca\x02/\xb7C7v\xbd\x1c=\x07\x903\xf17\xaf\xbf\x8eqY!\x9fe\xec\x1f\x9e\xde\x0f^\xfb\xe3\x92\x92\x92\xadK\x97.}\xfe\xe8\xd1\xa3v\x94Y\x16b?\x83\xb3\x99\xaa\xc9\x05\x13\xb17\xe8aZ\x99\xf9\xea\xab\xaf\xc439#\x06\xb2q\xd3\xde\x8c\x08\x98\xfe\xe4,Y\\\xd6\x80\x1bc\xca\xd1\x99\x9e3\xbfj\xe6O\xe7\xd7\xd6\xd6\xda`\xe1\xd6\xaa\xaa\xaa\xf4\xe6\x19\x0b\xfeM\xb1fN5\xf5\xbc\xc5^\xd2z\xf3\xa2?\x1cW\xb3\x06\x11=\x82.\xc5\xb3g\xcf\xda\x17/^\xfc$h\xef\x97\x91\x805\x9e#F\x8cx\xf6\xae\xbb\xee\xba\x1b\xe3\xc8\x80\xb7\xda\x01\x88\xa8\xbfO%\x0e\xc0\xb4jY0O\x9f\xf4\x9d\xae\xeb\xe5\xa8L\xc2i\xd7(\xb8\xf7:r\x15\x0b\xe43\xa2\x8d!\'\'\xe7\x9e\xd5\xabW\xff\xc7\x89\x13\'\xec\x17/^\x14!\xcfG\n\x97\x11\xb3\xf882E\xff\x89\t\xf8Wf|\xdf[\xf0\x90*\xd8B\xbc\xa9\xa7\xfeB\xab\xf3LU}, <\x0e\x87\xb3\xab\xe6T\x83\xaf\xc7\xe53\xde\x93\x86\x8d_~\xfe\xfc\xf9\x0c\xc4\xa7\xf4\xb3\xb3\x97,R\xed\xd9?0\xcat~YY\xd3\xf8\x97\x1d\x07:O~q&\xa4}1}lc\xe9\x8f\x1e `q\xa6\xc1\x1b\xc6"\xa6.\t\xa7D\x18k\x03@t\x84\xbb7l\xd8\xb0\xe5\xa5\xa5\xa5chQ\x02\x00\t\x06\x0f\x14A\xa7\x16=\xc0$\x030-F \xb52)\x08`\\\xf3\x9f\xb1\x0c\r\xd4\xbc`\xc5\x8a\x15\x8f\xc0\xd0\x89\t\x84xS|1\xde\x07\x88.\x1a\x1b\x1b\xed\xb6\xec\xc2\x05\xa4\xcc\xde\xd8\xe1u{/lxf}\xdb\xce\xb7\x0f"\xf5W-\x85C\x87\x8cya\xc7\xe3i\x05E\x85\xc66\x9av\xbc\xf1_-o\xaf\xfe\x00r>\xa1\xa0\xa8`\xd8\x93\xaf?\x909\xfa\x9a\x92^\x01!mP\xd3\xa4[\xa6\xb6\xef\xdfrR*\x1c\xf9K\xde\xd0\xcf\xa5\x8dk\xde\xe8\xf9\xcb\xbb\x156\x9b\xcd\xd3&\xcbv\xdbu\xb3\xcb\x86\xfe\xea_\x1f\x15\xd2\xec_/\x15\xe5\x16\xfd\xec\xac\x90\xfd\x9f\x99u\xd5\xed\xf7\xdcs\xcf\xaf\x14\xfd`q\x00\xf8\xbaU\xabV\xbd\x89Xx\x1e\xb4\xc8&M\x9a4r\xed\xda\xb5\x0f!\xe6\xe9\xc7\x9b5{\xf6\xecG\xb6l\xd9\xf2,\x01\xa8o\x83\xc0\xa1\x12\x87\x0e\x02\x98\x0e\xad\xe6\xe5\xf4r\x81\xbf\x03\x80\xe9\xeace\xd3\xa6M\x077l\xd80\x07\xc0e!>\x0fA\xac\x9e<w\xee\xdc\x1f"\x07\x19\xae\x1f\xeb\xa0A\x83\x1eA>\xb0\x05a\xa6\x1e\xb9\x83J\xf9I\x84\x84+$\x0b\x17\xe2-\x07\x90\x00\x08DC\xaa\x9068\xc8\xa3\xbe\xf8x\xb7\xb4\x7f\xfb\x1f\x91\tW\x81\xde\xaarU\xcfg\xed\xbb6o\x08\xf1\xbc\xcf+\xfe\xea}\xef\x95M\x18\xf0)L\xa4\xba\xd0\xa2\x1ci\xf9\xdd??o\x94\xf3\r\x1a3\xd3y\xf3\xdd7\xa1\x9fAA\xcf\x1f,\xff\x93\xf5\xd0\xff\xbc?v\xec\xd8s\xe3\xc7\x8f\xaf\x1d3f\xcc\xd9\x8c\xd3\x87\xca\x9b\xb7\xbc\xf4JpL\xb6du\\\xf3\xa3[\x91\xa1\xf6G\x922G\xef\x15\xa0\xfe\xc6\'\x9f|r%\x0c\xf5#\xb4S\x856NC\xee\xc0\xc3\x0f?\xbc\x02t\xdc\xa1\x97E&{\x03\xe6\x9ba\xa4X\x022Di8\x8c\x9eJ\'\x01o\xbc\x86\x12I\xc6\xb8\xba\x86\x0f\x1f~\tI\xdfY\xd4\xcb\x9fn\xdf\xbe\xfd\x9d\x05\x0b\x16,;|\xf8\xf0\x11\xbd,\x19\xda\xacY\xb3\xe6\xc1\xb9b-Lqf\x01\x8ex\xd0\x1b\x11\xd0\x905\x84V/\xd4\x1c\x80\xa5\xb5"\x89q\x80\xd6\x1c\xa07\x87R\xfe\xfb=!\xf4\xd9Xw\x10r\xcdW_}u\xeb\x94)SZ\x01\xb4#\xdb\xdby\xd6\xdb\xd6z1\xa8=\x85\xe5+\x85\xa3\xa6\x1b\x9f\x97w\xff~\xfb\xd0\xa1C\xa9\x9f\xf6\xa9S\xa7v\x94\x95\x95\xb5\xa1\x8dV\xb1b\xc7\x1e_WW{P\x1b\xf6\xec\t\xf3\xe7\xcf\xbf\xc1\xa8\xdc\xf2\xf2\xf2?`\x0e\xa7\x91\x01\xb7\xa0\r\xc7\xb5\xd7^\xeb\x80\x92\x9bq\xadz\xdf\xbe}\xdb\xf5\xb2\xc0,\x13I\xd7\xc8\x80\x07\xeb\xce \xa5j\x0b\x16!\xb4\x1b0\x04\xe3u\xba\x84\x18\xeb\x81\x819\xd1\xbe\x03\xbah\xc6\xdf\x970\xb7\xba5k\xd6\xac\x83W{\xf4\xf2\xf0\xdckP\xb7[\x11\x1e-\xf1,\xbc\xc4M\xd1d\xc9T\xd3\x19\x18\x8f\x133\xb3]\x88s=Px\x0f(\x84\x1d<x\x90j\xc2n\xa3\x9c\x85\xa9-\xa0\xc1n\x00\xe4\x02\xd02\xb2V\x15\x89[z\x8f\xa48\xf5\xb2>\x97\xdbF\xecg\xd1]\x93[\x1b\xaa\xb2\xba\x9b\xeb\x8bKK{&N\x9c\xe8\xa6Wm\x00E\x86\xf2)\xcb\xec\xeaq\xb9\x9a8{\xff\xdc^\x1aM\xcf\x19\x8b\xc4\xe4\xa8\x91\x9e\xdfy\xe7\x9d\x0f\xa0\xccN\xd0\xb2\x13\n\x95\xe9\x1a\xbcI\x82\x9c\x88\xac\xb5b\xce\x9c9\xf7\xeb\xe5\xe1eC\x03\x1e\xac\xa7\xe8\x00-\xeb\x95j\x96\xa2),\x004\t,\xe6%=\xd0%d\xfe\x1eT\'*\xf2\x82\xf3\xc8\xdek\xa1\xa7\xde\xb0\x85\xfax\x1c\x98\x84*\x03>F\x1d\x9c\\\x0c\xfez\xe0\xc6e\x19\x9b\x8czP\x01`\xfe\x15!\x14\xeb\nb\xa4\x14"\'\xa6I(\x03\xfc\x05<\xd5\x8f8U<#;\x99\x00\xcd\xe8\xda\x97d\xd1\xd8\x0f\xe3E\x05J\xf1\xc1\xf2%\x02\x17\xed\xfb\xcf\xfe\xfd\xfb\xd3\xe2\x88\xaf\xcb\'9\xf5m\xc8^I\x84\'\xa4\x19\x01\x86|\xcf\x90!C\xbc\x04.=O\xd7\xa8n\x86az\xc1<V\xa3<\x19P \xc9\xd2\x03\x070\x8d\x8b\x17\xbc\x11\xc8H\x00k\x06\xe3\x7f^\xab\xd7\x19\xc6$#[v\xd3\t\xc3\x91\x8d\xf2\x94\xb0Q\x88\xec\xd3$K\xd7a\xf0:\x03\xb95\xcf\x13X\xfe\xc1\xd2\xf2\x9f(\x8a\x9c\xdb \x07\xa3S\xe9\x1eb\x8e\x9f\xbb C\xcf1\xcc\x86\t:Y\x05\x13\xa2U\xaa\xa0~\xb2\xf2\xae\xc6\xc4Y\xc0\x03tK~\xfe\xbf\xd5\x8c\xec\x11L\'\xefm\xaa\xbdHJ4\x8e\x15\xa0\x92\xa1(\x01p\xb5\xc5\x7f\xbf\xc2A\xd7\xdf7\xca\xef\xdf\xbf\xbf\x16\tP\xd0X\xd0g\x96\x06r\xefB\x03\x01\x8c\xf1e\xe9\xe5\xb4\xdaV\xa5O\xfdux\xe7\x0c*\xa1h\xd5+\x8c\x07\x92\xa3\x14\xe8\xe5\xe1\xd15\x89\xe0$$\xfa\xb6&4\xa5W9\xa3\xe2i\xe9-L!\xdf\x0b\x88&~Y9F9\xe4+\xdeS\x9f\x9e4>\xef\xb8s\xd5\xdd\xb0b\x91\x00\x81\x82\xfcI\x1f\xc5\xa6\xd6\x1b\xee\x9b\xae\x8ai\x05zY\xb9\xa9\xf6\x1c%3a\x92\x1e\x06\xaf\xf4?\x8b\xa4\x8a\xaa\x02\x91\xea\xee\xe9\xd3\xa7O\x82W\xdf\xa1\x97\x05\xc5\xb7!)k\x035\xf6\xe8\xaf\xe7\xe5\xe5\x95\x92G\xd1\xba6\xadgc\x0c\xb4\x9cjA6<\xd3PNu\xc3\x98e$H\'\xf4\xd7\xe1\xb5\xa3Pg\xcfF\xdfVZ>\x85\x9c\x7f)\x17\xa7\xb8|\xf9\xf2{a|\x85\x86\xc4\xf04\x19&\x98K\xd5a\xc4\xc2`\xc5\x92\xf1`\xb2b\x16\x00\xce@O~@\x03r\x9aesF9\xdc`\x9a\x9c\xde\xf2\x19\x19\x88>\xb03\xde"K\xe5\x9b\x0eK\xb7,n\x132\xfa\xe5\xf5\x1aM\xe1U\xbf8<\xea\xefOX>/\xdf\x0f%K\x88K\x96#\x03\xa7\x97\xb9\xae\xbey\x8d\x9e\xcf\x99\xecs+\xfb7\x7fh\x9d5c\x84q\x0c\x14\xc7\x90\x98\x8dD\xec\x1b\x08\xa0\xa9\x86\xb5 \xe9\x9b\x91\x9f\x9f\xff3z\xd7\xa0\x97?u\xea\xd4_A\xff\xdd\x00\xe8XQQ\xd1\xe4\xc0u\x02h\xf1\xe2\xc5\xff\x88\x12\xeaU\x80+\x02\x80\xb4\'\x9ex\xe2\xb7\x00\xb3P\xff<=G\xe5\xdc\xae]\xbb\xfe\x8c\xbc\xe1\'\xfaq\xe0\xfb\xaf1\x87\xc2m\xdb\xb6\xbdF!\r\xb9\x88e\xd1\xa2EK\x10&\xfe\xc98f\xc8\x94CF\xd2\x98\x8f\x99uH3\x00\x87\xdd\x9b\x14\x020\x0b\xf6`\x02\xf12p\x06\x805Z\x0b\xc8\xd1g@.\x08`\xc1"\x81\xa6\xba\xbc\x95{\xb6\xd9\xae\x9f\xb7D7\x84L\xe7\xe8\x99o\xec)\x9eR-\xf6\xb4\xedSl\x99\xe3@\xcd7\xf9G\xa9\x8f}\xd5G>\xc8\xe8nn\x84r\x07\x1b\xc7@\x8b\xfc(\x8d\xeeDR\xb88\x1c3\xe9b\xaf\xfb]\x1c\xc8\x17:+**\xca\x91\xed\xfe\\/\x8brp\xe9c\x8f=v\'\x8c\xbe\x01\xfd\x94\x04h[\x7f\xe0\xb9\xbd\xf0\xba\xee\xe3\xc7\x8fW\x03\xec#\x88\xb3\xd7\xea\xebl|\x7fl\xe9\xd2\xa5\x0f`LU\x98o\t\xd8\xa5\x9f\xb1\r$~[\xab\xab\xab/!)\xa4\xa4LI\x96\xa2Y,\xcb\xd0\xbc\xd8H\xd1~\xef\xd6\x80\x0bxy\xa8\x9cz\x19\xd0\x80\x9c\x06.S4\x90\xbf\xa6hA\x86b\x9d\xb6?\xbe\xf0\x9e\xaf\xe1\xcc\x17\xc6vd\xc1:\xd6\xd3o\xe0\x03RZ\xd6M\xc6{R{s\xbd\xb5|=\x01\xe3D\x8c\x0f\xa1h\xd0\xaa\r\xf4\x9c\x16m\x05\tt\xeb\xd9\xb0a\xc3\xbf\x802/\xc0\x10\x9c\'O\x9e\xac\xf9\xf2\xcb/w\x85\xa1\xfb\xc1\x00\x97@\x0bYW\xae\xac\xac\xdcN\xc0"\x81\xeb\x06;8\xd7\xad[\xf7,\xd8\xc3\x1dn\xfd\x19mL\xa5\xcf\x90\x90\xe4p\\\xd8\xb8q\xe3\xdb\xc8\xf2]0\x06)\xdeM\x10B\x14\x81p\xdf)v\xb1p1\x98 #\xa0B\x803\xcai\xd759\x7f\xc2\xa5\x1a\xc0\xf5\xcb\xc1\x9fAInP\x98C\xd8\xfa\xcc3\xbe\x8b\xa7\x8f\x99YC\x96\xda\x9a\x1a\xf8\xb7\x96=V u\xd4![v\x01`\xc9(\x83\xd8I\xcb~\xb6Hm\x80*;\xd6\xaf_\xffk\x94,\x1f#&w\x80\xcd\x9d\x00\xa9c\xd3\xa6M\xafC\xe1\x17\xcd\x8c\xa3\xaa\xaa\xea\xe3\xe7\x9e{\xee\xdf\xf1\x9c\x13\x94\xeb\x02\xbdw\xc3Xj\xdf|\xf3\xcd\xa7\x10s/\x99i\x03\x89U\xfd\x8a\x15+\x96\xa2|\xaa\xc38\\\xa3F\x8d\x92\xb4\x1d\x98\x91\xe2o\x08v\xf1P4\xafQ*u \x1bi\x84\x13,2(J\td\x95\x94\x1d\x1bS\xfd\xcbbV\x19\xf7\x14\xbd!P"D\x8e\xcd\x05-\xe5Y\xc8\x83]T\x02Y\x9a\x9a\xce\xd6\xbfr\xef2\xf7\x9c\xa5w\x89\x93~\xf8c!3;\'\xe4maOg\xa7z\xeeX\x85}\xebo^\x1d<dH\xd3\xd0\xa1\xc3\xbbh]\xf8r\xfe\x16\x92/\xf8\r\xccx\xbd\xb5\xb5\xb5\t\x9e\xfa\xd1\xce\x9d;\xdf\x83\x01\x9c\x03\x05\xb7\x83\xca\xbb\xe1=*\xd8\x89\xea\xd3Z\xc4\xdd\xfb\x97-[\xf6pii\xe9\xdf\xa5\xe9w\xd1}\xbd\xd2\xd7\xf1\xc9\'\x9f\xbc\x87Z\xfb]Z\xecA\x1b=\xf8\xf4![\x96\xd0&w\xe8\xd0\xa1\x0fO\x9c8Q\xbfp\xe1\xc2{&O\x9e<+\\\x1b0\x84N\xc4\xfe\x0fW\xae\\\xf92\x00\xbdT\\\\\xdc\x8e\xba\xddC\xef\x89\xe3d\\\xff\x0b\xffX;\xe9\x83\x8ai\xea\x04t\xe2nyh\xf2\xb5P`\x01\xf4d\xc1\xb5vd\x8f-Y\x93\'S\xf9\xa1jI\x08e|\x9e\xb6\xe57NG&:\x00\xa5\x90\x08\xb9\xb6\x82A\x83Zl\xd7\\C\xefP\x15\xad\x80\xa7g\xbc\x19\xeb~\xfa\x0b8N>\x14\x99\x8e\xf6\xbb@\x8b\xad\xb9c\xc6\xb8\xc9jiA\x80\x8c\xa5\xa9\xfc\xf5\xb7:\xdf[\xfb\xdfr\xd9-\x93\xf9\xa1%%|vA\x01\xf3\xba{\xb8Kgj\xac\x1fo;\x88\xfe\xda\x06\r\x1b\xd6\x818\xd5\r\x8f\xf1\x9e?\x7f>=\x1c\x90HT\xbck\xd7\xae}\x15\xe3\xdf\x08\xc5g\xe3\xbe\r\xedS\x02\xd3\x831v\x11\x9d\x96\x94\x948\x01\x8e\x0b\xca\xa5\xfa\x9eA\xc1\x0c\x9e\xdf\x81\xf1)/\xbf\xfc\xf2\xf3\x98\xd3\x86\xdbo\xbf}&dFc|\x19\xf0\xec\xe6\x9a\x9a\x9a\xea\x03\x07\x0eT\xd28@\xa7\x1d\xa3G\x8fv\x0e\x1f>\xdc\x07\xdd\xd0F\x86^\xf6\xc2\xb8|/\xbd\xf4\xd2\x1a\xf4\xbd\x1emL\xa76\xa0\x07\x7f\x1b\x88\xb5\xd5{\xf6\xec\xa9D\x93\xedH\x02\xdb\xa0\x87\xce\xb2\xb22\x0f\xc5^\x80\xcd"xoBIVX\xe01a\t@\xb8\xe9\x9d\x01&\xdc\xe5\xcf\x14\xb2\xb2\xe8\x05\xbb\x1b\xb5\x9d/\xe0\x99\x14/0`*-\x9a\xb2\xb3\xb3;I\x0e\x13\x970`7\x94/\x05\xe4\xf0\x9c\x04\nt\x83\xfa\x1dPn7\xe4\x05\x02\x1d\x93\xf3\xc0\xf2\xbdP\x10\xd1\x12)Y\xc6\xf3n\xb4\xd9\xe9\xac\xfb\xac\xd1WS\xb1\x97\xde\xe6\x10S\x00\x18_\xbf\xe2b\x0f=\x83\xb6\xdd\xf4\xc2_\xf3TEK\xe2\x82\'-\x8an\x02\x11\x9fm\xf0\xaaf\xaa7\xc1"d\xb82B\x82\x0fc\xa2\x05\x0f\x1f\xfa\x0e\xec.\xa1q\xaa\xe3\xc7\x8f\'\x19\x89\x16"P\xde\xb4!\x81\xaa\xdf\xbbw\xaf\x95vg\xd0\xcb\x03\x8cQB\xff.\xb4\xed\x81\x9e\xdc0\x12\x89\x16}\x02;T`\xac$H\xa1\xc7\x0b\xdau\x81\xaa\x1d\x1f}\xf4\xd1\x85\xf2\xf2rz\xed\xc8\x13\x03bL>\x9a\x03t\xe6\x06-\x93\x81{5p\xd5\x08/\xf8#\xbd\xec\x0f\x028\xd2\xbe\xdb\x10\xafF\xa7\xe4\x0eD\x172\x00v\x91\x00Y\x16\x94\xab\x80\xceh5\x88\x0b\xac\x0c\xa1\xf4\xf0\x00|\xda\x15\xd1\x13\xf0~\xbaN[sp=\xb0\x04\xa7\xa2M/\xd5\x8a\x90s\xd1D\x89\x05\xa8\xde\x83\xc1\xf8\xb7\xfa\x90\x0c\x0cCF)\xe2C\xbd\xea\x82\x81Q\x1dL\'mh\xf3o\x9fA\xbf\xb2n\xcb\x8e\xbf\x14\xd2\xe7\x01F\x0fF\xdb=\x18\x87\x87\xb6\xe3\x04\x16\\\xa8_\xda\xae\x13\xd8\xe3E\xfd\x06\x9e\xa1\xfd^\x18\x03\xc3\xb8d\xcc\xd5\x87\x8c\x18A\xa1S\xa4\xda\x97\x168\xa8|!\xc3$c\x84G\xd2X\x14\xe3\xfe.\xfa\x1b}\x92\x01I\x98\x8b\x17s\x11\xa9\x0e\x0f\xb4A\xef*\x02m`|\xfe\xf9\xd0\xdc\x0c\x9ek6\x19\x8e\xba\xab2\x12U3tL\xab02J\x06%\xda\x9b\r\xda\xccM\x8a\x82\x15\xcb\xd1\xdex@at\xaa\xb0T9\xd6\x1emP\x9eB}\xd3\xe2\x02\x01H\xfb\xa0h-\x98\xac\x9b\x00\xa1\x8d~\xba\xad2\x02\x8cE\r\xe7\xc1\x94C\xc0\xc0\xbcS\xa6L\xf1\xc4\x91`\xfa7\x12\xd2IF\x04\x10}\xa8\xc1y\x00$\x04\x96\x1b\xc9\x08\x08DZF\x8dD\x8bd\xd8t\x12m\x83i\xfcm \xf6\x0b\xda~,\xa6\x197\x0b\x03jLo\xe5b\xfct%\xaa\xe7r\xd1\x7f\x94\xc5\xe2\xd8\xac\x1d\x0e\xech\xbfl\x0f\xca\x05hA@\x032\xeavU-\xf62-K7\xd6\xbaT\r\xa8a6\x9c3\xb3\xdf5\xc3\xa4w\xb5q\xd5\xa5\xfa6\x90@\xfaO2\xda0\xf7\x13\xfd\x8c\x9aE\xc7\x02\x993\x01x\xb4\x1f3s1\xc0f\x11\xde\x94\xf0\x9c\xb9_\xbc\xf3\xba\x954Z\xd0P\xc3\x01L\xe0R\xcd\x1e\xa5\xd40\xb3R\x94\xaa\xdfO\xb18\xfe6\x03n\xcc$+\x1a\xc8\x1c\x17\xfbg\x8b\xf1\xee\xefeQ\xbc\x9a\x8f\xc2\x04Q\x7f\x0c\xad\xbd\xe9\xf1\'5\xba\xe5\xf1@\x92\xa5\xd0\x8b\x91\x04<\xb8\xaf\x80\x8d\x17`\xd34-&\xe0\x85\xa9\x04\xd7\x8c\x12x\x93\xcc\x10\xf4\x9d\x92\x15z\ry\xf4\xe8\xd1J$R\x8f"V\xe6\x12\xb0H\xa2\xda\x00\xbaG+\xd3X\x9c@\xf6%\xb8\xb1\xc0bf\xea\xdeD\xcb\xa4h\x9e\x13\xeb\xc53\x9fb\xc5\xf0f\xc6H^\x8bD\xc6\x07\x80\xebq\xfe\x19\tY:\xed\x15\x03\xf0T\xa6\xb9\x00\xb4\xccE\xfe\xd1W_\x81\xcb\xe2\xbc\xcfLzx\xc4\xb6\xc5\x04\xe83\xd6\xbf\xfa1\xbd\xdb EF\x106\xc6SmJ\x1b\xe8ii\x155\'\xbdu\xea\xa2\x92\x8a6\x1bPmM\xf5\xfc7\xc8s\x13\xa5\xee\x98\x8c FP\x90)%F\xc9b\xe3\x016\x95\n\xec=\xa8\x9e\xa5]\x10S\xa7N%/\xf5\xd1~\xee@\xcdN\x89W~~~\\\x8a\xe2R\x7f$\xeb\xcd\xb1\xda`\x91\x16:\xe2M\x86bu\x96\xcc\x8f\xb9\x93\xa2wPt\xef\xbc\x00h2@\xf6\xe5\x7f\x1c`\t\xde7\xf5\xef\x0f\xc58\x004\xeb\xb9\xc9(\xc7\x0cK\xf4u,d)\x9a\xcb\x95\x1e\x9b\xe9,\xda,\xd0\xf1xa\xb2\x93Ku\x12\xc7\xfa\xf8\xfe\x95\xf4\xf0\xa4\xb2\xe8D@J\x952\x92M\xe2\xf8\x14x\xc4\x95\xfeg0,\xd5\xcf\x89\t4\xc0\xff?N\x96O\xf2~\xb2\x8a\xfd&\xfd\x83TSc\x11\xfb\xd8\xca\xf8>\x9e\x14\xdf\x87\x00\xb0o\x13\x90\xa9\x04\xf8J+)\x91,\x9c\xbf\x02c\xfc\xa6\xfe\xbb\xe3\xa0\xe3\xff\x04\x18\x00\xa2#\xab\x055\x97\xa0\x08\x00\x00\x00\x00IEND\xaeB`\x82\n'


class CreateAppFormTestCase(unittest.TestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        # setup the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_create_with_required_fields(self):
        """
        Test creating an app using the app form and known good data.
        """

        app_form = AppForm(DEFAULT_APP_DATA)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        expected_app = generate_app(None, **DEFAULT_APP_DATA)

        model_eq(app, expected_app, check_primary_key=False)

    def mptest_create_with_required_field_missing(self):
        """
        Test that each required field of the app form generates a validation
        error when it is missing by removing each of them from known good data
        and confirming that the correct validation error appears.
        """

        for key in DEFAULT_APP_DATA.keys():
            incomplete_data = copy.copy(DEFAULT_APP_DATA)
            del incomplete_data[key]

            app_form = AppForm(incomplete_data)

            ok_(not app_form.is_valid(),
                "%s was missing, but the AppForm validated." % key)

            eq_(app_form._errors.keys(), [key])

    # TODO: this test fails with Jenkins because the form requires the zip
    # package to do the image resizing. Figure out how to get it on there.
    # def mptest_create_with_img_file(self):
    #     files = {
    #         'img_file': SimpleUploadedFile('icon.png', IMAGE_DATA, content_type='image/png')
    #     }

    #     app_form = AppForm(DEFAULT_APP_DATA, files)

    #     ok_(app_form.is_valid(),
    #         "The AppForm was passed valid data but failed to validate:\n%s" %
    #             app_form._errors.as_text())

    #     app = app_form.save()

    #     data = copy.copy(DEFAULT_APP_DATA)
    #     expected_app = generate_app(None, **data)

    #     model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

    #     image_data = app.icon_blob.open().read()
    #     eq_(image_data, RESIZED_IMAGE_DATA)

    #     ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))

    def mptest_create_with_img_url(self):
        """
        Test app creation using the app form and sending the URL of a known
        image as the img_url.
        """

        data = copy.copy(DEFAULT_APP_DATA)

        data['img_url'] = DEFAULT_IMG_URL

        app_form = AppForm(data)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        data = copy.copy(DEFAULT_APP_DATA)
        expected_app = generate_app(None, **data)

        model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

        image_data = app.icon_blob.open().read()
        eq_(image_data, DEFAULT_IMG_URL_DATA)

        ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))


class EditAppFormTestCase(unittest.TestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        # setup the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.app = generate_app(None)

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_edit_with_required_fields(self):
        """
        Test editing an app using the app form and known good data.
        """

        app_form = AppForm(DEFAULT_APP_DATA, instance=self.app)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        expected_app = generate_app(None, **DEFAULT_APP_DATA)

        model_eq(app, expected_app, check_primary_key=False)

    def mptest_edit_with_required_field_missing(self):
        """
        Test that each required field of the app form generates a validation
        error when it is missing by removing each of them from known good data
        and confirming that the correct validation error appears.
        """

        for key in DEFAULT_APP_DATA.keys():
            incomplete_data = copy.copy(DEFAULT_APP_DATA)
            del incomplete_data[key]

            app_form = AppForm(incomplete_data, instance=self.app)

            ok_(not app_form.is_valid(),
                "%s was missing, but the AppForm validated." % key)

            eq_(app_form._errors.keys(), [key])

    # TODO: this test fails with Jenkins because the form requires the zip
    # package to do the image resizing. Figure out how to get it on there.
    # def mptest_edit_with_img_file(self):
    #     files = {
    #         'img_file': SimpleUploadedFile('icon.png', IMAGE_DATA, content_type='image/png')
    #     }

    #     app_form = AppForm(DEFAULT_APP_DATA, files,
    #                        instance=self.app)

    #     ok_(app_form.is_valid(),
    #         "The AppForm was passed valid data but failed to validate:\n%s" %
    #             app_form._errors.as_text())

    #     app = app_form.save()

    #     data = copy.copy(DEFAULT_APP_DATA)
    #     expected_app = generate_app(None, **data)

    #     model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

    #     image_data = app.icon_blob.open().read()
    #     eq_(image_data, RESIZED_IMAGE_DATA)

    #     ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))

    def mptest_edit_with_img_url(self):
        """
        Test app editing using the app form and sending the URL of a known
        image as the img_url.
        """

        data = copy.copy(DEFAULT_APP_DATA)

        data['img_url'] = DEFAULT_IMG_URL

        app_form = AppForm(data, instance=self.app)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        data = copy.copy(DEFAULT_APP_DATA)
        expected_app = generate_app(None, **data)

        model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

        image_data = app.icon_blob.open().read()
        eq_(image_data, DEFAULT_IMG_URL_DATA)

        ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))


DEFAULT_ADUNIT_DATA = {
    'name': 'Test AdUnit',
    'device_format': 'phone',
    'format': 'full',
    # This field is not marked as required in the model or form, but is
    # effectively made required by AdUnitForm.clean_refresh_interval.
    'refresh_interval': 0,
}


class CreateAdUnitFormTestCase(unittest.TestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        # setup the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_create_with_required_fields(self):
        """
        Test creating an adunit using the adunit form and known good data.
        """

        adunit_form = AdUnitForm(DEFAULT_ADUNIT_DATA)

        ok_(adunit_form.is_valid(),
            "The AdUnitForm was passed valid data but failed to validate:\n%s" %
                adunit_form._errors.as_text())

        adunit = adunit_form.save()

        expected_adunit = generate_adunit(None, None, **DEFAULT_ADUNIT_DATA)

        model_eq(adunit, expected_adunit, check_primary_key=False)

    def mptest_create_with_required_field_missing(self):
        """
        Test that each required field of the adunit form generates a validation
        error when it is missing by removing each of them from known good data
        and confirming that the correct validation error appears.
        """

        for key in DEFAULT_ADUNIT_DATA.keys():
            incomplete_data = copy.copy(DEFAULT_ADUNIT_DATA)
            del incomplete_data[key]

            adunit_form = AdUnitForm(incomplete_data)

            ok_(not adunit_form.is_valid(),
                "%s was missing, but the AdUnitForm validated." % key)

            eq_(adunit_form._errors.keys(), [key])

    def mptest_create_with_refresh_interval(self):
        """
        Test refresh_interval validation by passing a bad value an confirming
        the correct validation error appears.
        """

        invalid_data = copy.copy(DEFAULT_ADUNIT_DATA)
        invalid_data['refresh_interval'] = -1

        adunit_form = AdUnitForm(invalid_data)

        ok_(not adunit_form.is_valid(),
            "refresh_interval was missing, but the AdUnitForm validated.")


class EditAdUnitFormTestCase(unittest.TestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        # setup the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_edit_with_required_fields(self):
        """
        Test editing an adunit using the adunit form and known good data.
        """

        adunit_form = AdUnitForm(DEFAULT_ADUNIT_DATA)

        ok_(adunit_form.is_valid(),
            "The AdUnitForm was passed valid data but failed to validate:\n%s" %
                adunit_form._errors.as_text())

        adunit = adunit_form.save()

        expected_adunit = generate_adunit(None, None, **DEFAULT_ADUNIT_DATA)

        model_eq(adunit, expected_adunit, check_primary_key=False)

    def mptest_edit_with_required_field_missing(self):
        """
        Test that each required field of the adunit form generates a validation
        error when it is missing by removing each of them from known good data
        and confirming that the correct validation error appears.
        """
        for key in DEFAULT_ADUNIT_DATA.keys():
            incomplete_data = copy.copy(DEFAULT_ADUNIT_DATA)
            del incomplete_data[key]

            adunit_form = AdUnitForm(incomplete_data)

            ok_(not adunit_form.is_valid(),
                "%s was missing, but the AdUnitForm validated." % key)

            eq_(adunit_form._errors.keys(), [key])

    def mptest_edit_with_refresh_interval(self):
        """
        Test refresh_interval validation by passing a bad value an confirming
        the correct validation error appears.
        """

        invalid_data = copy.copy(DEFAULT_ADUNIT_DATA)
        invalid_data['refresh_interval'] = -1

        adunit_form = AdUnitForm(invalid_data)

        ok_(not adunit_form.is_valid(),
            "refresh_interval was missing, but the AdUnitForm validated.")
