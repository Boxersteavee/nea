from FlaskServer import app
debug = True
#TODO: change debug to False before deployment
def main():
    app.run(debug=debug)

main()