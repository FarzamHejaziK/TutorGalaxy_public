import pkgutil
import importlib
import tiktoken_ext

# Iterate over the submodules of tiktoken_ext
for finder, name, ispkg in pkgutil.iter_modules(tiktoken_ext.__path__, tiktoken_ext.__name__ + '.'):
    print(f"Checking module: {name}")
    try:
        # Import the module
        module = importlib.import_module(name)

        # Try to fetch ENCODING_CONSTRUCTORS
        encoding_constructors = getattr(module, "ENCODING_CONSTRUCTORS", None)

        if encoding_constructors is None:
            print(f"Module {name} does not define ENCODING_CONSTRUCTORS")
        else:
            print(f"Module {name} defines ENCODING_CONSTRUCTORS: {encoding_constructors}")
    except Exception as e:
        print(f"Error while checking module {name}: {e}")
        
from flask import Flask
import tiktoken 
import tiktoken_ext


encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
encoding.encode('1000000000')
app = Flask(__name__)


@app.route('/')
def hello_world():

    return "My Lambda App works"


if __name__ == '__main__':
    app.run()