from versio import config
from versio.tools.localversio import LocalVersio

_instance = LocalVersio()

def instance():
    return _instance

def startInstance(user, password):
	pass
    
def logout():
    global _instance
    _instance = LocalVersio()
