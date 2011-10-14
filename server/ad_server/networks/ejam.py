from ad_server.networks.mocean import MoceanServerSide
from ad_server.networks.server_side import ServerSideException  
""" Ejam is built on top of mocean. """
class EjamServerSide(MoceanServerSide):
    pub_id_attr = 'ejam_pub_id'
    network_name = 'eJam'
