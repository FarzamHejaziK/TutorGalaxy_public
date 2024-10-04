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
