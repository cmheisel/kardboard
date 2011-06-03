from kardboard import app

class Kard(app.db.Document):
	key = app.db.StringField(required=True, unique=True, primary_key=True)
	title = app.db.StringField()
	backlog_date = app.db.DateTimeField(required=True)
	start_date = app.db.DateTimeField()
	done_date = app.db.DateTimeField()