# Автоматизированный учебный курс


First, clone the repository to your local machine:

```bash
https://github.com/Vildan16/Evaluation-system.git
```

Create Virtual Env and Install the requirements:

```bash
cd django-schools
python3 -m venv env
source ./env/bin/activate
pip install -r requirements.txt
```

Create the database and run the development server:

```bash
cd django_school
python manage.py migrate
python manage.py runserver
```

The project will be available at http://127.0.0.1:8000, Login using::

**Teacher**

+ username: `teacher`
+ password: `teacher`

**Student**

+ username: `student`
+ password: `student`
