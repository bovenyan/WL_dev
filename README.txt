run in virtual Env:
	$ source wikkitEnv/bin/activate

Try uwsgi
	$ uwsgi --socket 0.0.0.0:8000  --protocol=http -w wikkit_dev:app

exit virtual Env:
	$ deativate
