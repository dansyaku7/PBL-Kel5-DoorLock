from flask import Flask, render_template, url_for, session, flash, request
app = Flask(__name__)

@app.route("/")
def login():
    return render_template("tampilandepan.html")

if __name__ == '__main__':
    app.run(debug=True)