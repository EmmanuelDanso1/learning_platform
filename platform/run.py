from waitress import serve
from realmind import create_app

app = create_app()



if __name__ == "__main__":
    print("Starting server at http://127.0.0.1:5000 ...")
    serve(app, host='127.0.0.1', port=5000)
