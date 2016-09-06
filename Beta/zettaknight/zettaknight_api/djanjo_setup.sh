#!/bin/bash

### necessary things ##########
set -u #error on unbound variables
set -e #exit if any error is encountered
set -o pipefail #make sure each output in pipestatus is checked, not just the final return
###############################

### vars ######################
running_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#setopts="${running_dir}/setopts.sh"
#source $setopts || { echo "failed to source $setopts"; exit 1; }

working_dir="${running_dir}/django" #directory where django will install
project_name="zettaknight"
application_name="api"
superuser='root'
email_recipients="mcarte4@g.clemson.edu rgoodbe@g.clemson.edu"
###############################

######## files ################
file1="${working_dir}/${application_name}/serializers.py"
file2="${working_dir}/${application_name}/views.py"
file3="${working_dir}/${project_name}/urls.py"
file4="${working_dir}/${project_name}/settings.py"
###############################



###### functions ##############

function put_everything_back () {
    
    echo -e "\n ### putting everything back the way $0 found it ###\n"
    
    echo "removing installed pip packages"
    pip uninstall django==1.5.6 djangorestframework==2.4.8 pygments -y
    
    echo -e "\nremoving project: $working_dir"
    if [ -e "$working_dir" ]; then rm -rf $working_dir; echo "removed $working_dir"; fi
    
    echo -e "\nremoving files"
    if [ -e "$file1" ]; then rm -rf $working_dir; echo "removed $file1"; fi
    if [ -e "$file2" ]; then rm -rf $working_dir; echo "removed $file2"; fi
    if [ -e "$file3" ]; then rm -rf $working_dir; echo "removed $file3"; fi
    if [ -e "$file4" ]; then rm -rf $working_dir; echo "removed $file4"; fi
    
    echo -e "\ndone"
    
}

###############################


###############################
#### script start #############
###############################

trap "put_everything_back; exit" INT TERM EXIT

# Create the project directory
if ! [ -e "$working_dir" ]; then 
    mkdir -p "$working_dir" 
    echo "created $working_dir"
fi

cd $working_dir

echo "installing pip packages"
pip install django==1.5.6 djangorestframework==2.4.8 pygments

# Set up a new project with a single application
echo -e "\ncreating django project: $project_name"
django-admin.py startproject ${project_name} .
cd $working_dir

echo -e "\nstarting app: $application_name"
django-admin.py startapp $application_name

#create user named admin with a password of password

echo -e "\ncreating: $file1"
cat > "$file1" << EOF
from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

EOF

echo -e "\ncreating: $file2"
cat > "$file2" << EOF
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from ${working_dir}.${application_name}.serializers import UserSerializer, GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
EOF

echo -e "\ncreating: $file3"
cat > "$file3" << EOF
from django.conf.urls import url, include
from rest_framework import routers
from ${working_dir}.${application_name} import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
EOF

echo -e "\ncreating: $file4"
cat > "$file4" << EOF
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '${working_dir}/${project_name}/sqlite3.db', # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#u!ij2aculhhf@!7o)8bab&a&r3m\$lpn05!lssq%_wg6n+e7#8'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = '${project_name}.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '${project_name}.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',

)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}



REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 10
}
EOF



#sync database for first time
echo -e "\nsyncing database"
cd $working_dir
{
sleep 2
echo "no"
} | python manage.py syncdb

python manage.py createsuperuser --username="${superuser}" --email="${email_recipients}"

#run the server

trap - INT TERM EXIT #end trap
echo -e "\nstarting server"
python manage.py runserver 2>1 > /dev/null &


exit 0





