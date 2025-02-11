from flask import Flask, render_template, url_for

app = Flask(_name_)

@app.route("/")
def index();
return render_template("index.html")

if _name_ = "_main_":
app.run(host= "0.0.0.0")
