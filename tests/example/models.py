from django.db import models


class CheckOne(models.Model):
    title = models.CharField(max_length=100)
