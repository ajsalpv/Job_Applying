
from langgraph.prebuilt import create_react_agent
import inspect
import sys

with open("sig.txt", "w") as f:
    try:
        sig = inspect.signature(create_react_agent)
        f.write(str(sig))
        f.write("\nParams: " + str(list(sig.parameters.keys())))
    except Exception as e:
        f.write(str(e))
