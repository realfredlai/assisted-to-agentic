from django.contrib import admin

from api.models import User, Application, Configuration

admin.site.register(User)
admin.site.register(Application)
admin.site.register(Configuration)
