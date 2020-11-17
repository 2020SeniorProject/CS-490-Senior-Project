heroku buildpacks:clear
heroku buildpacks:add --index heroku/python
heroku ps:scale web=1
web: gunicorn app:app
