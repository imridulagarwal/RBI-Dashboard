# RBI ATM/POS/Card Statistics Dashboard - Deployment Instructions

This document provides instructions for deploying the RBI ATM/POS/Card Statistics Dashboard application to a production environment.

## Package Contents

The deployment package contains:

- `src/` - The Flask application source code
- `requirements.txt` - Python dependencies
- `generate_sample_data.py` - Script to populate the database with sample data

## Deployment Options

You can deploy this application to any Flask-compatible hosting environment, including:

1. **PythonAnywhere** - A cloud platform designed for hosting Python web applications
2. **Heroku** - A cloud platform that supports Python applications
3. **AWS Elastic Beanstalk** - Amazon's PaaS for deploying web applications
4. **Google Cloud Run** - Google's serverless container platform
5. **Your own server** - Any server with Python and pip installed

## Deployment Steps

### Option 1: Deploy to Your Own Server

1. **Extract the package**:
   ```
   unzip rbi_stats_app_package.zip
   cd rbi_stats_app_package
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Generate sample data** (optional, but recommended for first-time setup):
   ```
   python generate_sample_data.py
   ```

5. **Run the application**:
   ```
   python -m flask --app src.main run --host=0.0.0.0 --port=5000
   ```

6. **For production deployment**, use a WSGI server like Gunicorn:
   ```
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 'src.main:app'
   ```

### Option 2: Deploy to PythonAnywhere

1. Sign up for a PythonAnywhere account at https://www.pythonanywhere.com/
2. Upload the zip file to your PythonAnywhere account
3. Extract the package in your PythonAnywhere account
4. Create a new web app with Flask
5. Set the source code directory to the extracted package directory
6. Set the WSGI configuration file to point to `src.main:app`
7. Install the requirements using the PythonAnywhere console:
   ```
   pip install -r requirements.txt
   ```
8. Run the sample data generation script:
   ```
   python generate_sample_data.py
   ```
9. Reload the web app

### Option 3: Deploy to Heroku

1. Sign up for a Heroku account at https://signup.heroku.com/
2. Install the Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
3. Extract the package locally
4. Create a new file named `Procfile` with the following content:
   ```
   web: gunicorn src.main:app
   ```
5. Add `gunicorn` to requirements.txt
6. Initialize a Git repository:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
7. Create a Heroku app and deploy:
   ```
   heroku create
   git push heroku master
   ```
8. Run the sample data generation script:
   ```
   heroku run python generate_sample_data.py
   ```

## Configuration

The application uses SQLite by default, which is suitable for small to medium deployments. For larger deployments, you may want to configure a more robust database like PostgreSQL or MySQL.

To configure a different database, modify the `SQLALCHEMY_DATABASE_URI` in `src/main.py`.

## Periodic Updates

The application is configured to check for updates from the RBI website daily. This is handled by the APScheduler library. No additional configuration is needed for this feature.

## Troubleshooting

If you encounter any issues during deployment:

1. Ensure all dependencies are installed correctly
2. Check that the database file is writable by the application
3. Verify that the port is not already in use
4. Check the application logs for specific error messages

## Support

If you need further assistance with deployment, please contact the development team.
