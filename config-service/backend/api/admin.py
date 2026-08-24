from django.contrib import admin

from api.models import Application, Configuration, User

admin.site.register(User)
admin.site.register(Application)
admin.site.register(Configuration)
