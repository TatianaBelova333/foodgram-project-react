# Foodgram Recipe Website

### Description
Website for posting and viewing recipes.
Unauthorised users are permitted to see all recipes and recipe authors' pages.
Authorised users may subscribe to other users, add and update their own recipes, add recipes to favorites and shopping cart and download ingredients from the shopping cart recipes.

### Technology Stack
* React
* Django
* Python 3
* Gunicorn
* Nginx
* Docker
* PostgreSQL

### Requirements & Compatibility
* Django==4.2.4
* django-filter==23.2
* djangorestframework==3.14.0
* djangorestframework-simplejwt==5.2.2
* djoser==2.2.0
* Pillow==10.0.0
* psycopg2-binary==2.9.7
* webcolors==1.13

### Installation
- Clone the repository
```
git clone [https://github.com/TatianaBelova333/kittygram_final.git](https://github.com/TatianaBelova333/foodgram-project-react.git)
```
- Create .env file in the project root directory as in the .env.example. Note that ALLOWED_HOSTS values in the .env file must be separated by a semicolon.

- Navigate from the project root directory to infra folder:
```
cd infra
```

- Build and run your app with docker compose from the project directory
```
docker compose up
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/
```
- To prepopulate database with initial data for testing, run the following command:
  ```
  docker compose exec backend python3 manage.py loaddata user ingredient measurementunit ingredientunit tagcolor tag recipe recipeingredientamount
  ```
- Alternatively, you can run this command (to prepopulate db with initial data for testing):
  ```
  docker compose exec backend python3 manage.py loadcsvdata
  ```

# Authors
[Tatiana Belova](https://github.com/TatianaBelova333)
