from bjut_tech import ConfigRegistry
from ._main import main

config = ConfigRegistry()

data = main(config)

print(data)
