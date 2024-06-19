pip3 install -r requirements.txt
python3.10 manage.py migrate
python3.10 manage.py collectstatic --noinput
