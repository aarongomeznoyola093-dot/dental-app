# app/db_session.py
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import logging
import sys
from cassandra.policies import RoundRobinPolicy

_session = None

def connect_to_db():
    """
    Se conecta a Cassandra y configura la sesión global.
    """
    
    global _session
    try:
        
        cluster = Cluster(
            ['127.0.0.1'],
            protocol_version=5,                  
            load_balancing_policy=RoundRobinPolicy() 
        )

        _session = cluster.connect('consultorio_dental')
        _session.row_factory = dict_factory
        logging.info(" Conexión a Cassandra exitosa.")
    except Exception as e:
        logging.error(f" Error fatal al conectar con Cassandra: {e}")
        sys.exit(1)
def get_session():
    """
    Devuelve la sesión de Cassandra ya conectada.
    """
    if _session is None:
        logging.warning(" La sesión de Cassandra no estaba iniciada. Conectando ahora...")
        connect_to_db()
    return _session

def close_db_connection():
    """
    Cierra la conexión a Cassandra (útil para apagar limpiamente).
    """
    global _session
    if _session:
        _session.cluster.shutdown()
        logging.info(" Conexión a Cassandra cerrada.")