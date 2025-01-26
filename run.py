from flask import Flask
from app import create_app

app = create_app()

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True)
