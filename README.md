# muspy

[muspy](https://muspy.com) is an album release notification service.

## Development

To set up development environment you need to install nginx and virtualenv, then run:

    % virtualenv env
    % source env/bin/activate
    % pip install -r requirements.txt

Edit your main `nginx.conf`:

    http {
        ...
        include /path/to/muspy/nginx-dev.conf;
    }

Update the project location in `muspy/nginx-dev.conf` and restart nginx.

Add this line to your `/etc/hosts`:

    127.0.0.1  muspy.dev

Go to the project directory and run `make db` to create an empty database.

Type `make run` and go to <http://muspy.dev/>. If static files don't load make
sure nginx has rx permissions for the `muspy/static` directory.

### Testing

You may run the test suite with `pytest`. If you need to set a debugger inside a test, you need to 
run `pytest -s`.

Coverage report can be shown with `pytest --cov`. A HTML report can be generated with 
`pytest --cov --cov-report=html`.


## Celery

Start worker and beat together (only suited for local development):

    celery --app=app worker --loglevel=INFO --beat --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    
Start worker and beat separately (on a production server):

    celery --app=app worker --loglevel=INFO
    
    celery --app=app beat --loglevel=INFO --scheduler=django_celery_beat.schedulers:DatabaseScheduler


## Frontend

./node_modules/.bin/webpack --config webpack.config.js --watch


Install dependencies with `npm install`.

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# build for production and view the bundle analyzer report
npm run build --report

# run unit tests
npm run unit

# run all tests
npm test
