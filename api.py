import argparse
import app
import os
import constant as const

# if __name__ == "__main__":
#     deepface_app = app.create_app()
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument("-p", "--port", type=int, default=8000, help="Port of serving api")
#     # args = parser.parse_args()
#     # waitress.serve(deepface_app, port=args.port)
# run the app using gunicorn
if __name__ == "__main__":
    deepface_app = app.create_app()
    deepface_app.run(port=8000)